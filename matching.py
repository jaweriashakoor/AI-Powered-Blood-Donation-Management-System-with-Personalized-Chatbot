# matching.py (continued)
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# --- Mock Donor Data ---
# In a real app, this comes from your database
data = {
    'age': [25, 30, 45, 22, 50, 35, 28, 41, 33, 55],
    'donations_last_12m': [2, 1, 5, 1, 3, 0, 1, 4, 2, 6],
    'months_since_last': [3, 8, 2, 12, 4, 24, 9, 2, 5, 1.5],
    'is_available': [1, 0, 1, 0, 1, 0, 0, 1, 1, 1]  # Target: 1 for Yes, 0 for No
}
donor_df = pd.DataFrame(data)


# --- Train the ML Model ---
def train_availability_model():
    """Trains a model to predict donor availability."""
    X = donor_df[['age', 'donations_last_12m', 'months_since_last']]
    y = donor_df['is_available']

    # Split data for training and testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale features for better performance
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Create and train the model
    model = LogisticRegression()
    model.fit(X_train_scaled, y_train)

    print("✅ Donor availability model trained successfully!")
    return model, scaler


# We will call this function once when the app starts
availability_model, scaler = train_availability_model()


def predict_donor_availability(donor_features):
    """
    Predicts if a donor will be available.
    `donor_features` should be a list like [age, donations_last_12m, months_since_last]
    """
    # Reshape and scale the input data
    features_scaled = scaler.transform([donor_features])
    prediction = availability_model.predict(features_scaled)
    probability = availability_model.predict_proba(features_scaled)

    # Returns 1 (Available) or 0 (Unavailable)
    return prediction[0], probability[0][1]

# Example Usage:
# new_donor = [38, 2, 6] # Age 38, 2 donations last year, 6 months since last
# prediction, probability = predict_donor_availability(new_donor)
# print(f"Predicted Availability: {'Yes' if prediction == 1 else 'No'} (Confidence: {probability:.2f})")