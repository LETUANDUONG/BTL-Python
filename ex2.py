import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import warnings
import time
warnings.filterwarnings('ignore')

# List of URLs for different statistical tables (corrected)
tables = [
    ('https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats#stats_standard', 'stats_standard'),
    ('https://fbref.com/en/comps/9/2024-2025/keepers/2024-2025-Premier-League-Stats#stats_keeper', 'stats_keeper'),
    ('https://fbref.com/en/comps/9/2024-2025/shooting/2024-2025-Premier-League-Stats#stats_shooting', 'stats_shooting'),
    ('https://fbref.com/en/comps/9/2024-2025/passing/2024-2025-Premier-League-Stats#stats_passing', 'stats_passing'),
    ('https://fbref.com/en/comps/9/2024-2025/gca/2024-2025-Premier-League-Stats#stats_gca', 'stats_gca'),
    ('https://fbref.com/en/comps/9/2024-2025/defense/2024-2025-Premier-League-Stats#stats_defense', 'stats_defense'),
    ('https://fbref.com/en/comps/9/2024-2025/possession/2024-2025-Premier-League-Stats#stats_possession', 'stats_possession'),
    ('https://fbref.com/en/comps/9/2024-2025/misc/2024-2025-Premier-League-Stats#stats_misc', 'stats_misc')
]

# Required statistics mapping to fbref column names
required_stats = {
    'Nation': 'Nation',
    'Team': 'Squad',
    'Position': 'Pos',
    'Age': 'Age',
    'Matches Played': 'MP',
    'Starts': 'Starts',
    'Minutes': 'Min',
    'Goals': 'Gls',
    'Assists': 'Ast',
    'Yellow Cards': 'CrdY',
    'Red Cards': 'CrdR',
    'xG': 'xG',
    'xAG': 'xAG',
    'PrgC': 'PrgC',
    'PrgP': 'PrgP',
    'PrgR': 'PrgR',
    'Gls/90': 'Gls_2',
    'Ast/90': 'Ast_2',
    'xG/90': 'xG_2',
    'xAG/90': 'xAG_2',
    'GA90': 'GA90',
    'Save%': 'Save%',
    'CS%': 'CS%',
    'PK Save%': 'Save%_2',
    'SoT%': 'SoT%',
    'SoT/90': 'SoT/90',
    'G/Sh': 'G/Sh',
    'Dist': 'Dist',
    'Cmp': 'Cmp',
    'Cmp%': 'Cmp%',
    'TotDist': 'TotDist',
    'Short Cmp%': 'Cmp%_2',  # Short passes completion percentage
    'Medium Cmp%': 'Cmp%_3',  # Medium passes completion percentage
    'Long Cmp%': 'Cmp%_4',  # Long passes completion percentage
    'KP': 'KP',
    '1/3': '1/3',
    'PPA': 'PPA',
    'CrsPA': 'CrsPA',
    'PrgP (Passing)': 'PrgP',
    'SCA': 'SCA',
    'SCA90': 'SCA90',
    'GCA': 'GCA',
    'GCA90': 'GCA90',
    'Tkl': 'Tkl',
    'TklW': 'TklW',
    'Att (Challenges)': 'Att',
    'Lost (Challenges)': 'Lost',
    'Blocks': 'Blocks',
    'Sh (Blocks)': 'Sh',
    'Pass (Blocks)': 'Pass',
    'Int': 'Int',
    'Touches': 'Touches',
    'Def Pen': 'Def Pen',
    'Def 3rd': 'Def 3rd',
    'Mid 3rd': 'Mid 3rd',
    'Att 3rd': 'Att 3rd',
    'Att Pen': 'Att Pen',
    'Att (Take-Ons)': 'Att',  # Dribble attempts in possession
    'Succ% (Take-Ons)': 'Succ%',
    'Tkld%': 'Tkld%',
    'Carries': 'Carries',
    'ProDist': 'PrgDist',  # Progressive distance in possession
    'ProgC (Carries)': 'PrgC',
    '1/3 (Carries)': '1/3',  # Corrected to match stats_possession
    'CPA': 'CPA',
    'Mis': 'Mis',
    'Dis': 'Dis',
    'Rec': 'Rec',
    'PrgR (Receiving)': 'PrgR',
    'Fls': 'Fls',
    'Fld': 'Fld',
    'Off': 'Off',
    'Crs': 'Crs',
    'Recov': 'Recov',
    'Won (Aerial)': 'Won',
    'Lost (Aerial)': 'Lost',
    'Won% (Aerial)': 'Won%'
}

def clean_player_name(name):
    """Clean player name by removing special characters and extra spaces."""
    return re.sub(r'[^\w\s]', '', name.strip()) if isinstance(name, str) else ''

def extract_first_name(name):
    """Extract the first name from the player name."""
    parts = name.split()
    return parts[0] if parts else name

def scrape_table(url, table_id, retries=7):
    """Scrape the specified table from the given URL with retries."""
    print(f"Scraping {url} for table ID {table_id}")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--ignore-certificate-errors')
    
    for attempt in range(retries):
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            table = wait.until(EC.presence_of_element_located((By.ID, table_id)))
            table_html = table.get_attribute('outerHTML')
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(table_html, 'html.parser')
            
            # Find rows
            rows = []
            for i in range(0, 1000):
                row = soup.find('tr', {'data-row': str(i)})
                if row:
                    rows.append(row)
            
            # Extract data
            data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) if cell.get_text(strip=True) else "N/a" for cell in cells]
                if row_data and len(row_data) > 1:
                    data.append(row_data)
            
            # Get headers from the table
            header_row = soup.find('tr', class_='thead')
            if not header_row:
                header_row = soup.find_all('tr')[0]
            headers = [th.get_text(strip=True) if th.get_text(strip=True) else f"Col_{i}" 
                       for i, th in enumerate(header_row.find_all(['th', 'td']))]
            
            # Create DataFrame
            if data:
                max_cols = max(len(row) for row in data)
                if len(headers) > max_cols:
                    headers = headers[:max_cols]
                elif len(headers) < max_cols:
                    headers = headers + [f'Col_{i}' for i in range(len(headers), max_cols)]
                
                df = pd.DataFrame(data, columns=headers)
                
                # Rename duplicate columns
                col_count = {}
                new_columns = []
                for col in df.columns:
                    if col in col_count:
                        col_count[col] += 1
                        new_columns.append(f"{col}_{col_count[col]}")
                    else:
                        col_count[col] = 1
                        new_columns.append(col)
                df.columns = new_columns
                
                # Clean invalid player rows
                df = df[df['Player'].notna() & (df['Player'] != 'Player') & (df['Player'] != '')].copy()
                
                # Check for duplicate players
                duplicates = df[df['Player'].duplicated(keep=False)][['Player', 'Squad', 'Pos']].drop_duplicates().values.tolist()
                if duplicates:
                    print(f"Duplicate players in {table_id}: {df[df['Player'].duplicated()]['Player'].tolist()}")
                    print(f"Duplicate details: {duplicates}")
                    df = df.groupby('Player').first().reset_index()
                
                print(f"Columns in scraped table {table_id}: {df.columns.tolist()}")
                df.to_csv(f'debug_{table_id}.csv', index=False)
                return df
            else:
                print(f"No data found in table at {url}")
                return None
        
        except TimeoutException:
            print(f"Timeout waiting for table at {url} (attempt {attempt + 1}/{retries})")
        except NoSuchElementException:
            print(f"Table with ID {table_id} not found at {url} (attempt {attempt + 1}/{retries})")
        except Exception as e:
            print(f"Error scraping {url}: {e} (attempt {attempt + 1}/{retries})")
        finally:
            driver.quit()
        time.sleep(5)  # Increased delay
    return None

def main():
    # Validate tables list
    print("Validating tables list...")
    for i, item in enumerate(tables):
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError(f"Invalid table entry at index {i}: {item}. Expected (url, table_id) tuple.")
    print("Tables list validated successfully.")

    # Initialize the main DataFrame with standard stats
    standard_url, standard_table_id = tables[0]
    df_main = scrape_table(standard_url, standard_table_id)
    if df_main is None:
        print("Failed to scrape standard stats. Exiting.")
        return

    # Ensure 'Player' column exists
    if 'Player' not in df_main.columns:
        print("No 'Player' column found in standard stats table. Exiting.")
        return

    # Clean player names and filter players with > 90 minutes
    df_main['Player'] = df_main['Player'].apply(clean_player_name)
    df_main['Min'] = pd.to_numeric(df_main['Min'].str.replace(',', ''), errors='coerce').fillna(0)
    df_main = df_main[df_main['Min'] > 90].copy()
    df_main['First_Name'] = df_main['Player'].apply(extract_first_name)

    # Initialize the result DataFrame
    result_df = pd.DataFrame({'Player': df_main['Player'], 'First_Name': df_main['First_Name']})

    # Map required columns from standard stats
    unmapped_columns = []
    for display_name, fbref_col in required_stats.items():
        if fbref_col in df_main.columns:
            result_df[display_name] = df_main[fbref_col].fillna('N/a')
            print(f"Mapped {display_name} to {fbref_col} from standard stats")
        else:
            result_df[display_name] = 'N/a'
            unmapped_columns.append((display_name, fbref_col, 'stats_standard'))
            print(f"Column {fbref_col} not found in standard stats for {display_name}")

    # Scrape and merge other tables
    for url, table_id in tables[1:]:
        df = scrape_table(url, table_id)
        if df is None or 'Player' not in df.columns:
            print(f"Skipping {url} due to missing table or 'Player' column")
            continue
        df['Player'] = df['Player'].apply(clean_player_name)
        # Merge with main DataFrame
        for display_name, fbref_col in required_stats.items():
            if fbref_col in df.columns:
                temp_df = df[['Player', fbref_col]].drop_duplicates('Player')
                merged_data = result_df[['Player']].merge(
                    temp_df,
                    on='Player',
                    how='left'
                )[fbref_col].fillna('N/a')
                if result_df[display_name].eq('N/a').all():
                    result_df[display_name] = merged_data
                    print(f"Mapped {display_name} to {fbref_col} from {table_id}")
                else:
                    print(f"Skipping {display_name} as it was already mapped")
            else:
                if result_df[display_name].eq('N/a').all():
                    unmapped_columns.append((display_name, fbref_col, table_id))
                print(f"Column {fbref_col} not found in {table_id} for {display_name}")

    # Log unmapped columns
    if unmapped_columns:
        print("\nUnmapped columns:")
        for display_name, fbref_col, table_id in unmapped_columns:
            print(f"{display_name} ({fbref_col}) not found in {table_id}")

    # Sort by first name
    result_df = result_df.sort_values('First_Name')

    # Drop the First_Name column
    result_df = result_df.drop(columns=['First_Name'])

    # Save to CSV
    result_df.to_csv('results.csv', index=False)
    print("Data saved to 'results.csv'")

    # Summary of N/a columns
    na_summary = result_df.eq('N/a').sum()
    print("\nSummary of 'N/a' columns in results.csv:")
    for col, count in na_summary.items():
        if count > 0:
            print(f"{col}: {count} 'N/a' values")

if __name__ == "__main__":
    main()