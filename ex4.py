import time
import os
import pandas as pd
import tracemalloc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from fuzzywuzzy import fuzz, process

def estimate_player_value(file_path):
    """Estimate player values using machine learning"""
    # Load data
    df = pd.read_csv(file_path)
    
    # Clean minutes column if necessary
    if df['Playing Time: minutes'].dtype == object:
        df['Playing Time: minutes'] = df['Playing Time: minutes'].str.replace(',', '').astype(int)
    
    # Fix Transfer values format to int
    df = df.dropna(subset=['Transfer values'])
    df['Transfer values'] = df['Transfer values'].str.replace('€', '', regex=False)
    
    # Handle both M (millions) and K (thousands)
    df['Transfer values'] = df['Transfer values'].apply(
        lambda x: float(x.replace('M', '')) * 1_000_000 if 'M' in x 
        else float(x.replace('K', '')) * 1_000 if 'K' in x 
        else float(x)
    )
    
    df['Transfer values'] = df['Transfer values'].astype(int)

    # Select features
    features = [
        'Age',
        'Position',
        'Playing Time: minutes',
        'Performance: goals',
        'Performance: assists',
        'GCA: GCA',
        'Progression: PrgR',
        'Tackles: Tkl'
    ]

    X = df[features]
    y = df['Transfer values']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['Position'])
        ],
        remainder='passthrough'
    )
    
    # Model pipeline
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    # Train and evaluate
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Mean Absolute Error: {mae:,.0f} €")
    
    return model

def get_data():
    """Load and filter player data"""
    file_path = os.path.join('P1_RES', 'results.csv')
    df = pd.read_csv(file_path)

    # Clean minutes column
    df['Playing Time: minutes'] = df['Playing Time: minutes'].str.replace(',', '').astype(int)

    # Filter players with >900 minutes
    return df[df['Playing Time: minutes'] > 900]

def update_data(filtered_df):
    """Scrape transfer values from website"""
    player_dic = {name: '' for name in filtered_df['Name']}
    
    # Configure Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    
    try:
        # Automatic ChromeDriver management
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Scrape data
        url = 'https://www.footballtransfers.com/us/players/uk-premier-league/'
        driver.get(url)
        
        names, prices = [], []
        for cnt in range(22):
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            table = soup.find('table', class_='table table-hover no-cursor table-striped leaguetable mvp-table similar-players-table mb-0')
            if not table:
                print("Không tìm thấy bảng dữ liệu.")
                break

            # Extract names and prices
            names.extend([n.find('a').get('title') for n in table.find_all('div', class_='text') if n.find('a')])
            prices.extend([p.text.strip() for p in table.find_all('span', class_='player-tag')])
            
            print(f"Đã crawl {len(names)} cầu thủ")

            # Pagination
            try:
                driver.find_element(By.CLASS_NAME, 'pagination_next_button').click()
            except:
                print("Hết trang rồi! Dừng lại.")
                break

        # Match players using fuzzy matching
        for name, price in zip(names, prices):
            best_match, score = process.extractOne(
                name.lower(),
                [n.lower() for n in player_dic.keys()],
                scorer=fuzz.ratio
            )
            if score > 70:  # Only accept good matches
                matched_name = list(player_dic.keys())[list(map(str.lower, player_dic.keys())).index(best_match)]
                player_dic[matched_name] = price
            else:
                print(f"Không tìm thấy cầu thủ phù hợp: {name}")
                
        return player_dic
    
    finally:
        if 'driver' in locals():
            driver.quit()

def save_result(filtered_df, player_dic):
    """Save results to CSV"""
    filtered_df['Transfer values'] = filtered_df['Name'].map(player_dic)
    os.makedirs('P4_RES', exist_ok=True)
    file_path = os.path.join('P4_RES', 'MoreThan900mins.csv')
    filtered_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print("Đã lưu vào MoreThan900mins.csv")

def Task_1():
    """Task 1: Data collection and processing"""
    filtered_df = get_data()
    player_dic = update_data(filtered_df)
    save_result(filtered_df, player_dic)

def Task_2():
    """Task 2: Model training and prediction"""
    file_path = os.path.join('P4_RES', 'MoreThan900mins.csv')
    model = estimate_player_value(file_path)

    # Example prediction
    new_player = pd.DataFrame({
        'Age': [26],
        'Position': ['GK'],
        'Playing Time: minutes': [2250],
        'Performance: goals': [0],
        'Performance: assists': [0],
        'GCA: GCA': [0],
        'Progression: PrgR': [0],
        'Tackles: Tkl': [0]
    })

    predicted_value = model.predict(new_player)
    print(f"Estimated player value: {predicted_value[0]:,.0f} €")

def Problem_4():
    """Main workflow"""
    Task_1()
    Task_2()

if __name__ == '__main__':
    # Performance tracking
    tracemalloc.start()
    start = time.time()
    
    # Create output directory
    os.makedirs('P4_RES', exist_ok=True)
    
    # Run main workflow
    Problem_4()
    
    # Print performance metrics
    end = time.time()   
    print(f"\nThời gian chạy: {end - start:.2f} giây")
    current, peak = tracemalloc.get_traced_memory()
    print(f"Bộ nhớ hiện tại: {current / 1024 ** 2:.2f} MB")
    print(f"Bộ nhớ đạt đỉnh: {peak / 1024 ** 2:.2f} MB")
    tracemalloc.stop()