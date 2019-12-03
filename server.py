# echo server
import socket
import pandas_datareader as web
import datetime as dt
import matplotlib.pyplot as plt
import os
import tensorflow as tf
from data_processor import data_loader
from data_processor import train_test_split
from data_processor import data_scaler
from data_processor import generate_sets
from data_processor import build_model
from data_processor import graph_format
from data_processor import graph_data




# creates server socket
serverS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# ipv4 address of server
host = '192.168.220.68'

port = 9998

serverS.bind((host, port))

# queue up to 20 concurrent requests
serverS.listen(20)

# creates empty dataframe
df = None


def validate_tkr(tkr):
    global df
    # gets current date and sets appropriate variables
    end_d = dt.datetime.today()
    year = end_d.year
    month = end_d.month
    day = end_d.day
    end_d = dt.datetime(year, month, day)

    one_week_ago = dt.datetime.today() - dt.timedelta(days=7)
    year = one_week_ago.year
    month = one_week_ago.month
    day = one_week_ago.day
    one_week_ago = dt.datetime(year, month, day)
    try:
        df = web.DataReader(tkr, 'yahoo', one_week_ago, end_d)
        return 'success'
    except Exception:
        return 'error'


# retrieves data from online server
def gather_data(tkr):
    global df
    print(tkr)
    # block gets current date and sets appropriate variables
    d = dt.datetime.today()
    year = d.year
    month = d.month
    day = d.day

    start = dt.datetime(2017, 1, 3)  # (YEAR, MONTH, DAY)
    end = dt.datetime(year, month, day)
    df = web.DataReader(tkr, 'yahoo', start, end)
    fileName = 'datasets/' + tkr + '.csv'
    df = df.drop(['High', 'Low', 'Open', 'Close', 'Volume', ], axis=1)
    df.to_csv(fileName)
    return df  # this is only a df containing the dates and adj close value


# makes graph and returns file
def make_g(tkr):
    global df

    df, dataset = data_loader(f'datasets/{tkr.upper()}.csv')

    train, test = train_test_split(df, dataset)

    train_scaled, test_scaled = data_scaler(train, test)

    X_train, Y_train, X_test, Y_test = generate_sets(train_scaled, test_scaled)

    model = build_model(X_train, Y_train)

    model.save('model.h5')
    train_predict = model.predict(X_train)
    test_predict = model.predict(X_test)

    train_predict_plot, test_predict_plot = graph_format(dataset, train_predict, test_predict)

    graph_data(df, train_predict_plot, test_predict_plot)

    # TODO: Save model in different part of the file and load it here

    with open('imgFile.png', 'rb') as f:
        by = f.read()
    return by


def make_p(tkr):
    global df
    # add prediction code here
    df, dataset = data_loader(f'datasets/{tkr.upper()}.csv')
    train, test = train_test_split(df, dataset)
    train_scaled, test_scaled = data_scaler(train, test)
    X_train, Y_train, X_test, Y_test = generate_sets(train_scaled, test_scaled)

    model = tf.keras.models.load_model("model.h5")

    train_predict = model.predict(X_train)

    test_predict = model.predict(X_test)
    prediction = graph_format(dataset, train_predict, test_predict)[1]

    prediction = prediction[-2][0]
    return f'${round(prediction)}'


# print at start
print('Waiting for connection...')

while True:
    curr_conn, addr = serverS.accept()
    print(f'Log: connection made by: {addr}')
    tkr = curr_conn.recv(2048).decode('UTF-8')
    tkr_ending = tkr[len(tkr) - 1:len(tkr)]
    tkr = tkr[0:len(tkr) - 1]
    print(tkr, tkr_ending)
    if tkr_ending == 'v':
        curr_conn.sendall(validate_tkr(tkr).encode('UTF-8'))
    elif tkr_ending == 'g':
        curr_conn.sendall(make_g(tkr))
    elif tkr_ending == 'p':
        curr_conn.sendall(make_p(tkr).encode('UTF-8'))
    print('Send Successful')
    print('***END TRANSMISSION***\n')
