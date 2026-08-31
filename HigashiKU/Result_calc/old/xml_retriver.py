import xml.etree.ElementTree as ET
import pandas as pd
from config import XML_FILE

file_path = XML_FILE

def extract_link_attributes(file_path):
    """
    Parses an XML file and extracts the id, length, and width 
    attributes from all <Link> elements, returning a DataFrame.
    """
    link_data = []
    
    try:
        # 1. Parse the XML file.
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 2. Find all <Link> elements directly under the root (<Network> assumed).
        for link_element in root.findall('.//Link'):
            
            link_id = link_element.get('id')
            length_str = link_element.get('length')
            width_str = link_element.get('width')

            try:
                # Convert string attributes to float numbers
                length = float(length_str) if length_str else None
                width = float(width_str) if width_str else None
            except ValueError:
                print(f"Warning: Non-numeric length/width for link ID: {link_id}")
                length = None
                width = None

            # 3. Store the extracted data.
            link_data.append({
                'current_linkID': link_id, # Match the column name in the CSV data
                'length': length,
                'width': width
            })
            
    except FileNotFoundError:
        print(f"Error: The XML file '{file_path}' was not found. Please check CONFIG.XML_FILE path.")
        return pd.DataFrame()
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred during XML parsing: {e}")
        return pd.DataFrame()

    return pd.DataFrame(link_data)

def get_link_geometry():
    """Wrapper function to get geometry and calculate area."""
    df_geometry = extract_link_attributes(file_path)
    if not df_geometry.empty:
        # Calculate the area (denominator for density)
        df_geometry['area'] = df_geometry['length'] * df_geometry['width']
        # Drop redundant columns before merge
        df_geometry = df_geometry.drop(columns=['length', 'width'])
    return df_geometry

if __name__ == "__main__":
    # Example usage (requires config.py to run)
    geometry_data = get_link_geometry()
    if not geometry_data.empty:
        print("--- Extracted Link Geometry ---")
        print(geometry_data.head())
    else:
        print("No geometry data loaded.")