import xml.etree.ElementTree as ET
import pandas as pd

def extract_link_geometry(xml_file, output_csv):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    links = []
    
    # Iterate through all Group tags to find Links
    for group in root.findall(".//Group"):
        for link in group.findall("Link"):
            link_id = link.get("id")
            length = float(link.get("length", 0))
            width = float(link.get("width", 0))
            
            # Calculate Area
            area = length * width
            
            if area > 0:
                links.append({
                    "current_linkID": link_id,
                    "length": length,
                    "width": width,
                    "area": area
                })
    
    df = pd.DataFrame(links)
    df.to_csv(output_csv, index=False)
    print(f"Successfully extracted {len(df)} links to {output_csv}")

if __name__ == "__main__":
    extract_link_geometry("/home/kulla/CrowdWalk/crowdwalk/HigashiKU/Higashiv2.xml", "./HigashiKU/Result_calc/New/logoutput/link_geometry.csv")