
import pandas as pd

pd.read_csv("data/lorenz_attractor.csv", skiprows=3, header='infer', delimiter=',')