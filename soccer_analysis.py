import pandas as pd
import time
import requests
import streamlit as st

# Define retry parameters
retry_attempts = 5
delay_seconds = 30

# Hugging Face API setup
model_endpoint = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGINGFACE_API_KEY = "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"  # Replace with your API key if not using .env
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

# Function to get performance description and improvement suggestions from LLM for players
def get_performance_analysis(player_data):
    prompt = (
        f"Analyze the performance of a soccer player with the following metrics:\n"
        f"Average Speed: {player_data['average_speed_over_a_game']} m/s, "
        f"Goals: {player_data['no_of_goals_made']}, "
        f"Fouls: {player_data['fouls']}, "
        f"Yellow Cards: {player_data['yellow_card']}, "
        f"Red Cards: {player_data['red_card']}.\n"
        "Provide a performance description and suggest improvements."
    )
    
    for attempt in range(retry_attempts):
        response = requests.post(
            model_endpoint,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.75}}
        )
        
        if response.status_code == 503:
            print(f"Attempt {attempt + 1}/{retry_attempts}: Model is loading. Retrying in {delay_seconds} seconds...")
            time.sleep(delay_seconds)
        elif response.status_code == 200:
            generated_text = response.json()[0]["generated_text"].strip()
            return generated_text
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return "Unable to generate analysis due to repeated API errors."

# Function to analyze goalkeeper performance
def get_goalkeeper_analysis(goalkeeper_data):
    prompt = (
        f"Analyze the performance of a soccer goalkeeper with the following metrics:\n"
        f"Total Saves: {goalkeeper_data['no_of_goals_save']}.\n"
        "Provide a performance description and suggest improvements."
    )
    
    for attempt in range(retry_attempts):
        response = requests.post(
            model_endpoint,
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.75}}
        )
        
        if response.status_code == 503:
            print(f"Attempt {attempt + 1}/{retry_attempts}: Model is loading. Retrying in {delay_seconds} seconds...")
            time.sleep(delay_seconds)
        elif response.status_code == 200:
            generated_text = response.json()[0]["generated_text"].strip()
            return generated_text
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return "Unable to generate analysis due to repeated API errors."

# Function to analyze team data (players)
def analyze_team(df, selected_player_id):
    analysis = []
    player_data = df[df['player_id'] == selected_player_id].iloc[0]  # Get the selected player row
    
    if not player_data.empty:
        performance_data = {
            "player_id": player_data["player_id"],
            "average_speed_over_a_game": player_data["average_speed_over_a_game"],
            "no_of_goals_made": player_data["no_of_goals_made"],
            "fouls": player_data["fouls"],
            "yellow_card": player_data["yellow_card"],
            "red_card": player_data["red_card"]
        }
        
        analysis_text = get_performance_analysis(performance_data)
        analysis.append({
            "Player ID": performance_data["player_id"],
            "Analysis": analysis_text
        })
    return analysis

# Function to analyze goalkeeper data
def analyze_goalkeeper(df, selected_goalkeeper_id):
    analysis = []
    player_data = df[df['player_id'] == selected_goalkeeper_id].iloc[0]  # Get the selected goalkeeper row
    
    if not player_data.empty:
        goalkeeper_data = {
            "player_id": player_data["player_id"],
            "no_of_goals_save": player_data["no_of_goals_save"]
        }
        
        analysis_text = get_goalkeeper_analysis(goalkeeper_data)
        analysis.append({
            "Player ID": goalkeeper_data["player_id"],
            "Analysis": analysis_text
        })
    return analysis

# Streamlit UI
def main():
    st.title("Soccer Player & Goalkeeper Performance Analysis")
    
    st.sidebar.header("Upload CSV Files")
    team1_file = st.sidebar.file_uploader("Upload Team 1 Player Data", type=["csv"])
    team2_file = st.sidebar.file_uploader("Upload Team 2 Player Data", type=["csv"])
    goalkeeper1_file = st.sidebar.file_uploader("Upload Goalkeeper 1 Data", type=["csv"])
    goalkeeper2_file = st.sidebar.file_uploader("Upload Goalkeeper 2 Data", type=["csv"])
    
    if team1_file and team2_file and goalkeeper1_file and goalkeeper2_file:
        # Load CSV data
        team1 = pd.read_csv(team1_file)
        team2 = pd.read_csv(team2_file)
        goalkeeper1 = pd.read_csv(goalkeeper1_file)
        goalkeeper2 = pd.read_csv(goalkeeper2_file)

        # Allow the user to select between Player or Goalkeeper
        role_selection = st.sidebar.radio("Select Role to Analyze", ["Player", "Goalkeeper"])
        
        # Initialize analysis variables outside the if blocks
        player_analysis = []
        goalkeeper_analysis = []
        
        if role_selection == "Player":
            # Allow the user to select which player to analyze
            player_ids = team1['player_id'].tolist() + team2['player_id'].tolist()
            player_ids = list(set(player_ids))  # Remove duplicates
            selected_player_id = st.sidebar.selectbox("Select a Player ID to Analyze", player_ids)
            
            if selected_player_id in team1['player_id'].values or selected_player_id in team2['player_id'].values:
                selected_team = team1 if selected_player_id in team1['player_id'].values else team2
                player_analysis = analyze_team(selected_team, selected_player_id)
                st.subheader(f"Performance Analysis for Player ID: {selected_player_id}")
                st.write(player_analysis)
        
        elif role_selection == "Goalkeeper":
            # Allow the user to select which goalkeeper to analyze
            goalkeeper_ids = goalkeeper1['player_id'].tolist() + goalkeeper2['player_id'].tolist()
            selected_goalkeeper_id = st.sidebar.selectbox("Select a Goalkeeper ID to Analyze", goalkeeper_ids)
            
            if selected_goalkeeper_id in goalkeeper1['player_id'].values or selected_goalkeeper_id in goalkeeper2['player_id'].values:
                selected_goalkeeper = goalkeeper1 if selected_goalkeeper_id in goalkeeper1['player_id'].values else goalkeeper2
                goalkeeper_analysis = analyze_goalkeeper(selected_goalkeeper, selected_goalkeeper_id)
                st.subheader(f"Performance Analysis for Goalkeeper ID: {selected_goalkeeper_id}")
                st.write(goalkeeper_analysis)
            
        # Combine player and goalkeeper analysis and allow CSV download
        combined_analysis = player_analysis + goalkeeper_analysis
        if combined_analysis:
            st.download_button(
                label="Download Performance Analysis CSV",
                data=pd.DataFrame(combined_analysis).to_csv(index=False),
                file_name="performance_analysis.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()

