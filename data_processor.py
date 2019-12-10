from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM
from tensorflow.keras.callbacks import EarlyStopping
from typing import NoReturn, Tuple

# This python file will process the data and train it.
# No prediction will be done in here

WINDOW_SIZE = 10  # Sets a constant size for the rolling window used
scaler = MinMaxScaler(feature_range=(0, 1))  # set all data values between 0 and 1


def data_loader(filename: str) -> Tuple[pd.DataFrame, list]:
    """
    Function which reads in data from a csv file and uses pandas to turn it into a dataframe.

    Args:
        filename: String that represents the filename in csv format

    Returns:
        df: All stock information that was in the csv file that pandas read in
        dataset: List of tuples for every date and close value. Tuples are in the format (Date, Adj Close)


    """

    df = pd.read_csv(filename)
    df['Date'] = pd.to_datetime(df['Date'])
    dataset = list(zip(df['Date'], df['Adj Close'].values))

    return df, dataset


def train_test_split(df: pd.DataFrame, dataset: list) -> np.ndarray:
    """
     Splits data into train and test so it can be used in predictions

     Args:
         df: Any pandas dataframe that has been returned from the yahoo financial database
         dataset: dataset value that was returned from the data_loader function

     Returns:
         train: Training data that the model will use to fit itself (used to help the program learn).
         test: Data that will be hidden from model during training phase,
         and will be used to predict how accurate the model is

     #TODO: Make train_test_split work without the dataset


     """

    trainingRange = int(len(dataset) - 20)
    print("The training range is", trainingRange)
    train = df['Adj Close'].iloc[:trainingRange].values
    test = df['Adj Close'].iloc[trainingRange:].values
    train = np.reshape(train, (-1, 1))
    test = np.reshape(test, (-1, 1))

    return train, test


def data_scaler(action: str, train: np.ndarray, test: np.ndarray) -> np.ndarray:
    """
     Function which reads in data from a csv file and uses pandas to turn it into a dataframe.

     Args:
         action: String that represents the filename in csv format
         train: String that represents the filename in csv format
         test: String that represents the filename in csv format


     Returns:
         train_scaled: All stock information that was in the csv file that pandas read in
         dataset: List of tuples for every date and close value. Tuples are in the format (Date, Adj Close)

         test_scaled: If action == 'fit' {returns test_scaled array with all values scaled between 0 and one}
                      If action == 'inverse' {returns test_scaled array}

     """

    if action.lower() == 'fit':
        train_scaled = scaler.fit_transform(train)
        test_scaled = scaler.transform(test)

    elif action.lower() == 'inverse':
        train_scaled = scaler.inverse_transform(train)
        test_scaled = scaler.inverse_transform(test)

    return train_scaled, test_scaled


def to_sequences(data: np.ndarray, window_size: int) -> np.ndarray:
    x = []
    y = []

    for i in range(len(data) - window_size - 1):
        window = data[i:(i + window_size), 0]
        x.append(window)
        y.append(data[i + window_size, 0])
    return np.array(x), np.array(y)


def generate_sets(train_scaled: np.ndarray, test_scaled: np.ndarray) -> np.ndarray:
    X_train, Y_train = to_sequences(train_scaled, WINDOW_SIZE)
    X_test, Y_test = to_sequences(test_scaled, WINDOW_SIZE)
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
    print(X_test)
    print("=============================================================")
    print(f"X_trains shape is {X_train.shape} ; Y_Trains shape is {Y_train.shape}")
    print(f"X_tests shape is {X_test.shape} ; Y_Tests shape is {Y_test.shape}")
    print("================================================================================")
    print(X_train.shape, Y_train.shape)

    return X_train, Y_train, X_test, Y_test


def build_model(X_train: np.ndarray, Y_train: np.ndarray) -> tf.keras.models.Sequential:
    # TODO: Make sure tensorflow-gpu is running in tensorflow2
    model = Sequential()
    model.add(LSTM(64, input_shape=(X_train.shape[1], 1), return_sequences=True, activation='relu'))
    model.add(Dropout(.2))
    model.add(LSTM(32))
    model.add(Dropout(.2))
    model.add(Dense(1, activation='linear'))
    model.compile(loss='mean_squared_error', optimizer='adam', metrics=['accuracy'])  # adagrad?
    monitor = EarlyStopping(monitor='loss', patience=10, verbose=1, restore_best_weights=True)
    model.fit(X_train, Y_train, callbacks=[monitor], epochs=200)

    return model


def save_model(model):
    # TODO implement model saving
    return model


def graph_format(dataset: list, train_predict: np.ndarray, test_predict: np.ndarray) -> np.ndarray:
    """
    Function which formats train_predict and test_predict to be formattted for graphing in matplot

    Args:
        dataset:
        train_predict: train predictions
        test_predict: testing predictions

    Returns:

    """
    train_predict, test_predict = data_scaler('inverse', train_predict, test_predict)
    train_predict_plot = np.empty_like(dataset)
    train_predict_plot[:, :] = np.nan
    train_predict_plot[WINDOW_SIZE:len(train_predict) + WINDOW_SIZE, :] = train_predict

    test_predict_plot = np.empty_like(dataset)
    test_predict_plot[:, :] = np.nan
    test_predict_plot[len(train_predict) + (WINDOW_SIZE * 2) + 1: len(dataset) - 1, :] = test_predict

    return train_predict_plot, test_predict_plot


def graph_data(df: pd.DataFrame, train_predict_plot: np.ndarray,
               test_predict_plot: np.ndarray, tkr: str) -> NoReturn:
    """
    Function which reads in data from a csv file and uses pandas to turn it into a dataframe.

    Args:
        df: Pandas dataframe which contains original stock information
        train_predict_plot: train predictions --in array formatted for plotting
        test_predict_plot: testing predictions  --in array formatted for plotting
        tkr: Stock ticker

    """

    plt.clf()  # Clears currently plotted figure
    plt.title(f"{tkr.upper()} Stock Information")
    print(f"Test predict plots shape is {test_predict_plot.shape}")
    plt.plot(df['Date'], train_predict_plot, "-b", label="Train predict")
    plt.plot(df['Date'], test_predict_plot, "-y", label="Test predict")
    plt.plot(df['Date'], df['Adj Close'], "-g", label="Original")
    plt.xlabel('Date')
    plt.ylabel('Adj Close Price')
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.gcf().autofmt_xdate()
    plt.savefig('imgFile.png')
