import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import time
import pytz
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go

# Initialize Firebase
cred = credentials.Certificate(r'C:\Users\Shun-Xi Wu\Desktop\Firebase-515\esp8266-imu-firebase-adminsdk-b027u-3fd0303ca0.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://esp8266-imu-default-rtdb.firebaseio.com/'
})

# Function to fetch data from Firebase
# Function to preprocess accelerometer data
def preprocess_accel_data(data):
    # Convert data to numeric type
    data['xAccel'] = pd.to_numeric(data['xAccel'])
    data['yAccel'] = pd.to_numeric(data['yAccel'])
    data['zAccel'] = pd.to_numeric(data['zAccel'])
    
    # Define gravity acceleration (in m/s^2)
    gravity_acceleration = 9.8
    
    # Correct accelerometer data relative to the reference plane (subtract gravity)
    data['xAccel'] = data['xAccel'] - gravity_acceleration
    data['yAccel'] = data['yAccel'] - gravity_acceleration
    data['zAccel'] = data['zAccel'] - gravity_acceleration
    
    # Standardize accelerometer data to have the same magnitude
    accel_magnitude = (data['xAccel']**2 + data['yAccel']**2 + data['zAccel']**2)**0.5
    data['xAccel'] = data['xAccel'] / accel_magnitude * gravity_acceleration -2.2
    data['yAccel'] = data['yAccel'] / accel_magnitude * gravity_acceleration +5.2
    data['zAccel'] = data['zAccel'] / accel_magnitude * gravity_acceleration + 9.76
    
    return data

# Modify the fetch_data function to preprocess accelerometer data
def fetch_data():
    ref = db.reference('UsersData/readings2')
    pitch_data = ref.get()
    if pitch_data is None:
        return pd.DataFrame(columns=['Degree', 'Timestamp', 'xAccel', 'yAccel', 'zAccel']), False
    data_list = [
        {
            'Degree': v['degree'], 
            'Timestamp': v['timestamp'],
            'xAccel': v['xAccel'],
            'yAccel': v['yAccel'],
            'zAccel': v['zAccel']
        }
        for k, v in pitch_data.items()
    ]
    data_df = pd.DataFrame(data_list)
    data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp'].astype(int), unit='s')
    data_df['Timestamp'] = data_df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Los_Angeles')
    data_df = preprocess_accel_data(data_df)
    return data_df, True


# Streamlit page configuration
st.set_page_config(
    page_title="Real-Time Data Science Dashboard",
    page_icon="✅",
    layout="wide",
)

# Dashboard title
st.title("Real-Time / Live Data Science Dashboard")

# Creating containers for Degree and Accelerometer charts
degree_container = st.empty()
accel_container = st.empty()
time_container = st.empty()
latest_data_container = st.empty()

# Function to display the real-time Degree plot
def display_degree_plot(data):
    fig_degree = go.Figure()

    fig_degree.add_trace(go.Scatter(
        x=data['Timestamp'],
        y=data['Degree'],
        mode='lines',
        name='Degree',
        line=dict(color='blue')
    ))

    fig_degree.update_layout(
        title="Real-Time Degree Data (Last 10 Minutes)",
        xaxis_title="Time",
        yaxis_title="Degree"
    )

    degree_container.plotly_chart(fig_degree, use_container_width=True)

# Function to display the real-time Accelerometer plot
def display_accel_plot(data):
    fig_accel = go.Figure()

    fig_accel.add_trace(go.Scatter(
        x=data['Timestamp'],
        y=data['xAccel'],
        mode='lines',
        name='xAccel',
        line=dict(color='red')
    ))

    fig_accel.add_trace(go.Scatter(
        x=data['Timestamp'],
        y=data['yAccel'],
        mode='lines',
        name='yAccel',
        line=dict(color='green')
    ))

    fig_accel.add_trace(go.Scatter(
        x=data['Timestamp'],
        y=data['zAccel'],
        mode='lines',
        name='zAccel',
        line=dict(color='orange')
    ))

    fig_accel.update_layout(
        title="Real-Time Accelerometer Data (Last 10 Minutes)",
        xaxis_title="Time",
        yaxis_title="Acceleration (m/s^2)"
    )

    accel_container.plotly_chart(fig_accel, use_container_width=True)

# Function to display the current time
def display_current_time():
    now = datetime.now(pytz.timezone('America/Los_Angeles'))
    time_container.write(f"Current Time (Los Angeles): {now.strftime('%Y-%m-%d %H:%M:%S')}", 
                         unsafe_allow_html=True)

# Function to display the real-time plot and text data
def display_real_time_plot():
    all_data = pd.DataFrame(columns=['Degree', 'Timestamp', 'xAccel', 'yAccel', 'zAccel'])

    while True:
        data, connected = fetch_data()

        if connected and not data.empty:
            all_data = pd.concat([all_data, data]).drop_duplicates().reset_index(drop=True)
            now = datetime.now(pytz.timezone('America/Los_Angeles'))
            time_window_start = now - timedelta(minutes=10)
            recent_data = all_data[all_data['Timestamp'] >= time_window_start]

            # Display latest data in a large font
            latest_data_container.markdown("<h1>Latest Data</h1>", unsafe_allow_html=True)
            latest_data_container.write(recent_data.tail(1).to_html(index=False, justify='center', classes=["dataframe"], escape=False), 
                                         unsafe_allow_html=True)

            display_degree_plot(recent_data)
            display_accel_plot(recent_data)

        display_current_time()  # Move this function call outside of the if block

        time.sleep(1)

if __name__ == '__main__':
    display_real_time_plot()
