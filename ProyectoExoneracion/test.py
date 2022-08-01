import pandas as pd

estudiantes = pd.read_csv('./cedulas.txt', sep=" ", header=None, dtype = str)
estudiantes.columns = ["Identificacion"]


print(estudiantes)