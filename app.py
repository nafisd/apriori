from flask import Flask, render_template, request
import pandas as pd
from itertools import combinations

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('Sample - Store - Orders.csv')
df2 = df.drop(columns=['Postal Code', 'Sales', 'Quantity', 'Discount', 'Profit']).drop_duplicates()

result_df = df.groupby('Order ID')['Product ID'].agg(lambda x: ', '.join(x)).reset_index()
result_df['Product ID'] = result_df['Product ID'].str.split(', ')
transactions_dict = {product: index for index, product in enumerate(set(result_df['Product ID'].explode()))}

def find_key(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

result_df['Encoded Product ID'] = result_df['Product ID'].apply(lambda x: [transactions_dict[item] for item in x])

items = [item for sublist in result_df['Encoded Product ID'] for item in sublist]
unique_items = set(items)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    support_threshold = float(request.form['support_threshold'])
    
    candidate1_df = pd.DataFrame([(item, items.count(item)) for item in unique_items], columns=["itemset", "count"])
    candidate1_df['sup'] = (candidate1_df['count'] / len(result_df)) * 100
    freq_itemset1 = candidate1_df[candidate1_df['sup'] >= support_threshold].sort_values(by='sup', ascending=False).reset_index(drop=True)

    candidate2_list = [set(combo) for combo in combinations(freq_itemset1['itemset'], 2)]
    count_candidate2_df = pd.DataFrame([(combo, 0) for combo in candidate2_list], columns=['itemset', 'coount'])
    count_candidate2_df['sup'] = 0

    for i in range(len(result_df)):
        for j in range(len(count_candidate2_df)):
            if count_candidate2_df['itemset'][j].issubset(set(result_df['Encoded Product ID'][i])):
                count_candidate2_df.loc[j, 'sup'] += 1

    count_candidate2_df['sup'] = (count_candidate2_df['sup'] / len(result_df)) * 100
    freq_itemset2 = count_candidate2_df[count_candidate2_df['sup'] >= support_threshold].sort_values(by='sup', ascending=False).reset_index(drop=True)

    return render_template('result.html', freq_itemset1=freq_itemset1, freq_itemset2=freq_itemset2)

if __name__ == '__main__':
    app.run(debug=True)
