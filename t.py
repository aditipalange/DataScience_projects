import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import base64
import os
import webbrowser
import mysql.connector
import bcrypt
import re
if "login_status" not in st.session_state:
    st.session_state.login_status = False


# Set Streamlit app title
st.title("Sales Prediction Dashboard")

# Create a login page
def login_page():
    st.subheader("Login")
    username = st.text_input("Username", key="username_input")
    password = st.text_input("Password", type="password", key="password_input")
    login_button = st.button("Login")

    if login_button:
        # Perform authentication logic
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Check if the username and password match the database
                query = "SELECT * FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                result = cursor.fetchone()
                if result and bcrypt.checkpw(password.encode(), result[2].encode()):
                    st.success("Login successful!")
                    st.session_state.login_status = True
                    import_page()
                else:
                    st.error("Invalid username or password")
            except mysql.connector.Error as err:
                st.error(f"Error during login: {err}")
            finally:
                cursor.close()
                connection.close()
     # Add CSS styling for the login page
    st.markdown(
        """
        <style
        .login-page {
            background-image: url("background.jpg");
            background-repeat: no-repeat;
            background-size: cover;
            padding: 20px;
        }>
        #</style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-page">', unsafe_allow_html=True)
                 

# Create a registration page
def registration_page():
    st.subheader("Registration")
    email = st.text_input("Email ID")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    mobile_number = st.text_input("Mobile Number")
    
    if st.button("Register"):
        # Perform registration logic
        if not validate_email(email):
            st.warning("Invalid email ID. Please enter a valid email.")
        elif not validate_username(username):
            st.warning("Invalid username. Please choose a username with alphanumeric characters,Sprecial symbol and Integers only.")
        elif not validate_password(password):
            st.warning("Invalid password. Please choose a password with at least 8 characters, including uppercase, lowercase, and numeric characters.")
        elif not validate_mobile_number(mobile_number):
            st.warning("Invalid mobile number. Please enter a 10-digit mobile number only.")
        else:
            connection = create_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    # Check if the username is already taken
                    query = "SELECT * FROM users WHERE username = %s"
                    cursor.execute(query, (username,))
                    result = cursor.fetchone()
                    if result:
                        st.warning("Username already taken. Please choose a different username.")
                    else:
                        # Hash the password
                        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                        # Insert new user data into the database
                        query = "INSERT INTO users (email, username, password, mobile_number) VALUES (%s, %s, %s, %s)"
                        values = (email, username, hashed_password, mobile_number)
                        cursor.execute(query, values)
                        connection.commit()
                        st.success("Registration successful! Please login.")
                except mysql.connector.Error as err:
                    st.error(f"Error during registration: {err}")
                finally:
                    cursor.close()
                    connection.close() 
    # Validation functions

def validate_email(email):
    # Define email pattern
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def validate_username(username):
    # Define username pattern (alphanumeric and underscore only)
    pattern = r'^[a-zA-Z0-9@#$%*]+$'
    return re.match(pattern, username) is not None

def validate_password(password):
    # Password must contain at least 8 characters, including uppercase, lowercase, and numeric characters
    pattern = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$'
    return re.match(pattern, password) is not None
def validate_mobile_number(mobile_number):
    # Mobile number must contain exactly 10 digits
    pattern = r"^(0|91)?[6-9]{1}[0-9]{9}$" 
    return re.match(pattern, mobile_number) is not None

# Create a connection to the MySQL database
def create_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="aditi",
            database="sales",
            port=3307

        )
    except mysql.connector.Error as err:
        st.error(f"Error connecting to the database: {err}")

    return connection

# Create an import page
def import_page():
    st.subheader("Import CSV File")

    file = st.file_uploader("Upload CSV", type=["csv"], key="csv_uploader")

    if file is not None:
        # Read the CSV file
        df = pd.read_csv(file)
        st.success("File imported successfully!")

        # Store the DataFrame in the session state
        st.session_state.df = df

        # Provide option to perform prediction
        if st.button("Perform Prediction"):
            perform_prediction()

# Perform the sales prediction
def perform_prediction():
    # Get the stored DataFrame
    df = st.session_state.df

    # Process the data and generate graphs
    process_data(df)

    # Open the HTML file with graphs
    open_graphs()



# Process the data and generate graphs
def process_data(df):
    # Sort the sales data by item type
    df.sort_values(by='Item_Type', inplace=True)

    # Extract the sales values and item types
    sales = df['Sales'].values
    item_types = df['Item_Type'].values

    # Create a linear regression model
    model = LinearRegression()

    # Create a list to store the graphs
    fig_list = []

    # Set the figure size and spacing
    figure_width = 5  # Width of each figure in inches
    figure_height = 3  # Height of each figure in inches

    # Iterate through each item type and plot the graph
    for i in range(len(sales)):
        previous_sales = sales[:i + 1].reshape(-1, 1)

        if len(previous_sales) <= 1:
            continue  # Skip iterations with less than 2 sales entries

        # Fit the model to the previous sales data
        model.fit(previous_sales[:-1], previous_sales[1:])

        # Predict future sales
        future_sales = model.predict(previous_sales[-1].reshape(1, -1))

        # Get the item type for the current graph
        item_type = item_types[i]

        # Plot the previous vs predicted sales
        fig, ax = plt.subplots(figsize=(figure_width, figure_height))  # Adjust the figsize as desired
        ax.plot(previous_sales, label='Previous Sales')
        ax.plot(len(previous_sales) - 1, future_sales, 'ro', label='Predicted Sales')
        ax.set_xlabel('Time')
        ax.set_ylabel('Sales')
        ax.set_title(f'Item Type: {item_type}', color='white')  # Set title color to white

        # Add a text box with previous and predicted sales values
        text_box = f"Previous Sales: {previous_sales[-1][0]:.2f}\nPredicted Sales: {future_sales[0][0]:.2f}"
        ax.text(0.05, 0.95, text_box, transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(facecolor='white', alpha=0.5))

        ax.legend()
        fig_list.append(fig)
        plt.close(fig)

    # Save the graphs in an HTML file
    html_file = 'sales_graphs.html'
    with open(html_file, 'w') as f:
        f.write('<html>\n<head>\n')
        f.write('<style>\n')
        f.write('body { background-image: url("background.jpg"); background-repeat: no-repeat; background-size: cover; }\n')  # Add background image CSS
        f.write('.graph-container { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; }\n')  # Center align graph container
        f.write('.graph { display: inline-block; margin: 10px; }\n')  # Add spacing between graphs CSS
        f.write('.title { color: white; text-align: center; }\n')  # Set title color to white
        f.write('.info { display: flex; justify-content: space-between; }\n')  # Align previous and predicted sales info
        f.write('.previous-sales { float: left; }\n')  # Align previous sales to the left
        f.write('.predicted-sales { float: right; }\n')  # Align predicted sales to the right
        f.write('</style>\n')
        f.write('<title>Sales Prediction Dashboard</title>\n')  # Add title to the HTML file
        f.write('</head>\n<body>\n')
        f.write('<h1 class="title">Sales Prediction Dashboard</h1>\n')  # Add title to the HTML file
        f.write('<div class="graph-container">\n')

        for i in range(len(fig_list)):
            fig = fig_list[i]

            # Save the figure to a temporary file
            tmp_file = f'tmp_fig_{i}.png'
            fig.savefig(tmp_file, format='png', bbox_inches='tight')
            plt.close(fig)

            # Read the temporary file as bytes and encode in base64 format
            with open(tmp_file, 'rb') as img_file:
                img_bytes = img_file.read()
                img_base64 = base64.b64encode(img_bytes).decode()

            # Write the HTML code with the base64-encoded image
            f.write('<div class="graph">\n')
            f.write(f'<img src="data:image/png;base64,{img_base64}" style="width: {figure_width}in; height: {figure_height}in;">\n')
            f.write('<div class="info">\n')
            f.write(f'<div class="previous-sales">Previous Sales: {sales[i]:.2f}</div>\n')
            f.write(f'<div class="predicted-sales">Predicted Sales: {future_sales[0][0]:.2f}</div>\n')
            f.write('</div>\n')
            f.write('</div>\n')

            # Remove the temporary file
            os.remove(tmp_file)

            # Display two graphs side by side
            if i % 2 == 0:
                f.write('<div style="clear: both;"></div>\n')

        f.write('</div>\n')
        f.write('</body>\n</html>\n')

    st.success("Prediction completed successfully!")

# Open the HTML file with graphs
def open_graphs():
    html_file = 'sales_graphs.html'
    webbrowser.open(f'file://{os.path.abspath(html_file)}')

# Main logic
#if "login_status" not in st.session_state:
    #st.session_state.login_status = False

if not st.session_state.login_status:
    st.write("Please log in")
    # Display login form or other content
else:
    st.write("Welcome to the app!")
    # Display main content for authenticated users
login_page()
registration_page()
import_page()