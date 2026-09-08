import pandas as pd


def CreateMetaLocations():
    df = {"Location": str,
          "LOC_SHORT": str}
    return pd.DataFrame(df)


# Class to import locations into metadata
class MetaLocations:
    def __init__(self, dataframe = None):
        if dataframe is not None:
            self.dataframe = dataframe            
        
        self.columns = {"Location": str,
                        "LOC_SHORT": str}
        self.data = {col: [] for col in self.columns}
        
    def add_row(self, values):
        if len(values) != len(self.columns):
            raise ValueError("Number of values must match the number of columns.")
        
        for (col, col_type), value in zip(self.columns.items(), values):
            if not isinstance(value, col_type):
                raise TypeError(f"Value '{value}' is not of type {col_type.__name__} for column '{col}'.")
            self.data[col].append(value)
            
    def to_dataframe(self):
        return pd.DataFrame(self.data)
    def to_csv(self, filename, index):
        df = self.to_dataframe()
        return df.to_csv(filename, index = False)
    def get_dataframe(self):
        return self.dataframe

# Class to define 
class MetaTrials:
    def __init__(self):
        self.columns = {"Trial": str, 
                        "TRIAL_SHORT": str,
                        "TRIAL_ID": int, 
                        "TRT": int}
        self.data = {col: [] for col in self.columns}
    def add_row(self, values):
        if len(values) != len(self.columns):
            raise ValueError("Number of values must match the number of columns.")
        
        for (col, col_type), value in zip(self.columns.items(), values):
            if not isinstance(value, col_type):
                raise TypeError(f"Value '{value}' is not of type {col_type.__name__} for column '{col}'.")
            self.data[col].append(value)
    def to_dataframe(self):
        return pd.DataFrame(self.data)
    def to_csv(self, filename, index):
        df = self.to_dataframe()
        return df.to_csv(filename, index = False)
    
# Trial number of treatments and reps
class MetaTrialLocation:
    def __init__(self):
        self.columns = {"YEAR": int, 
                        "TRIAL_SHORT":str, 
                        "LOC_SHORT":str, 
                        "Trt": int, 
                        "Reps":int, 
                        "GS": str, # List with growth stages
                        "TRAITS" : str}
        self.data = {col: [] for col in self.columns}
    def add_row(self, values):
        if len(values) != len(self.columns):
            raise ValueError("Number of values must match the number of columns.")
        
        for (col, col_type), value in zip(self.columns.items(), values):
            if not isinstance(value, col_type):
                raise TypeError(f"Value '{value}' is not of type {col_type.__name__} for column '{col}'.")
            self.data[col].append(value)
    def to_dataframe(self):
        return pd.DataFrame(self.data)
    def to_csv(self, filename, index):
        df = self.to_dataframe()
        return df.to_csv(filename, index = False)
    
class GrowthStage:
    def __init__(self):
        self.GS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F10.1", "F10.5", "F11.1", "F11.2", "F11.3", "F11.4"]