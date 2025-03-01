import os
from notion_client import Client
import json
from pathlib import Path
import time
import re
import mimetypes
import requests
from urllib.parse import unquote
import base64

class NotionImporter:
    def __init__(self, token, parent_page_id, imgbb_key):
        self.notion = Client(auth=token)
        self.token = token
        self.parent_page_id = parent_page_id
        self.imgbb_key = imgbb_key
        self.MAX_CONTENT_LENGTH = 2000
        self.resources_path = None
        self.resource_files = {}

    def set_resources_path(self, root_path):
        """Set the path to the resources folder and cache all resource files"""
        self.resources_path = Path(root_path) / "resources"
        if not self.resources_path.exists():
            print(f"Warning: Resources folder not found at {self.resources_path}")
            return False

        print(f"\nScanning resources folder: {self.resources_path}")
        for file in self.resources_path.glob('*'):
            if file.is_file():
                self.resource_files[file.name] = file
                self.resource_files[file.name.lower()] = file
                self.resource_files[file.stem] = file
                self.resource_files[file.stem.lower()] = file
                print(f"Found resource file: {file.name}")

        print(f"Total unique resource files found: {len(set(self.resource_files.values()))}\n")
        return True

    def upload_to_imgbb(self, file_path):
        """Upload image to ImgBB and return the URL"""
        try:
            print(f"Uploading to ImgBB: {file_path}")
            with open(file_path, "rb") as file:
                # Convert image to base64
                base64_image = base64.b64encode(file.read()).decode('utf-8')
            
            # Make the API request to ImgBB
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": self.imgbb_key,
                "image": base64_image,
                "name": Path(file_path).stem
            }
            
            response = requests.post(url, data=payload)
            response.raise_for_status()  # Raise exception for bad status codes
            
            result = response.json()
            if result.get('success'):
                image_url = result['data']['url']
                print(f"Successfully uploaded to ImgBB: {file_path}")
                return image_url
            else:
                print(f"Failed to upload to ImgBB: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Error uploading to ImgBB: {str(e)}")
            return None

    def find_resource_file(self, image_ref):
        """Find a resource file using various matching strategies"""
        image_ref = unquote(image_ref)
        variations = [
            Path(image_ref).name,
            Path(image_ref).name.lower(),
            Path(image_ref).stem,
            Path(image_ref).stem.lower(),
        ]
        
        for variation in variations:
            if variation in self.resource_files:
                return self.resource_files[variation]
        
        print(f"Could not find image: {image_ref}")
        print("Tried variations:", variations)
        return None

    def process_content_with_images(self, content):
        """Process markdown content and extract image references"""
        if not self.resources_path:
            return content, []

        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        blocks = []
        current_text = ""
        last_end = 0
        
        for match in re.finditer(image_pattern, content):
            # Add text before the image
            text_before = content[last_end:match.start()]
            if text_before.strip():
                current_text += text_before
            
            # Process image
            alt_text = match.group(1)
            image_path = match.group(2)
            print(f"\nProcessing image reference: {image_path}")
            
            # If we have accumulated text, add it as a block
            if current_text.strip():
                blocks.extend(self.create_text_blocks(current_text))
                current_text = ""
            
            # Handle image
            resource_file = self.find_resource_file(image_path)
            if resource_file:
                print(f"Found matching resource: {resource_file}")
                image_url = self.upload_to_imgbb(str(resource_file))
                if image_url:
                    print(f"Successfully uploaded: {resource_file.name}")
                    blocks.append({
                        "type": "image",
                        "image": {
                            "type": "external",
                            "external": {
                                "url": image_url
                            },
                            "caption": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": alt_text
                                    }
                                }
                            ]
                        }
                    })
                else:
                    print(f"Failed to upload: {resource_file.name}")
            else:
                print(f"No matching resource found for: {image_path}")
            
            last_end = match.end()
        
        # Add remaining text
        remaining_text = content[last_end:]
        if remaining_text.strip():
            current_text += remaining_text
        
        if current_text.strip():
            blocks.extend(self.create_text_blocks(current_text))
        
        return blocks

    def create_text_blocks(self, content):
        """Create text blocks from content"""
        blocks = []
        chunks = self.split_content(content)
        
        for chunk in chunks:
            if chunk.strip():
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": chunk
                                }
                            }
                        ]
                    }
                })
        
        return blocks

    def split_content(self, content):
        """Split content into chunks that respect Notion's size limits"""
        chunks = []
        while content:
            if len(content) <= self.MAX_CONTENT_LENGTH:
                chunks.append(content)
                break
            
            split_point = self.MAX_CONTENT_LENGTH
            last_newline = content[:split_point].rfind('\n')
            
            if last_newline > split_point * 0.5:
                split_point = last_newline
            else:
                for char in ['. ', '! ', '? ']:
                    last_sentence = content[:split_point].rfind(char)
                    if last_sentence > split_point * 0.5:
                        split_point = last_sentence + 1
                        break
            
            if split_point == self.MAX_CONTENT_LENGTH:
                last_space = content[:split_point].rfind(' ')
                if last_space > split_point * 0.8:
                    split_point = last_space
            
            chunks.append(content[:split_point])
            content = content[split_point:].lstrip()
        
        return chunks

    def create_page(self, title, content, parent_id):
        """Create a new page in Notion with content and images"""
        try:
            print(f"Creating page: {title}")
            new_page = self.notion.pages.create(
                parent={"page_id": parent_id},
                properties={
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                }
            )
            
            if content:
                print(f"Processing content for page: {title}")
                blocks = self.process_content_with_images(content)
                
                if blocks:
                    print(f"Adding blocks to page: {title}")
                    self.notion.blocks.children.append(
                        block_id=new_page["id"],
                        children=blocks
                    )
            
            print(f"Successfully created page: {title}")
            return new_page["id"]
            
        except Exception as e:
            print(f"Error creating page {title}: {str(e)}")
            return None

    def import_structure(self, root_path):
        """Import the entire folder structure into Notion"""
        root = Path(root_path)
        
        if not root.exists():
            print(f"Error: The folder path '{root_path}' does not exist.")
            return
        
        # Set resources path and scan for files
        if not self.set_resources_path(root_path):
            return
        
        # Find the "My Notebook" folder
        notebook_folder = root / "My Notebook"
        if not notebook_folder.exists():
            print(f"Error: Could not find 'My Notebook' folder in {root_path}")
            return
            
        # Create main notebook page
        print("\nCreating main notebook page...")
        notebook_page_id = self.create_page("My Notebook", "", self.parent_page_id)
        
        if not notebook_page_id:
            print("Failed to create notebook page")
            return
        
        # Process each section (folder) in My Notebook
        print("\nProcessing sections...")
        for section_path in notebook_folder.iterdir():
            if section_path.is_dir():
                # Create section page
                section_name = section_path.name
                print(f"\nProcessing section: {section_name}")
                section_page_id = self.create_page(section_name, "", notebook_page_id)
                
                if not section_page_id:
                    print(f"Failed to create section page: {section_name}")
                    continue
                
                # Process each markdown file in the section
                print(f"Processing files in section: {section_name}")
                for md_file in section_path.glob("*.md"):
                    try:
                        # Read markdown content
                        print(f"\nProcessing file: {md_file.name}")
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create page for the markdown file
                        page_name = md_file.stem
                        page_id = self.create_page(page_name, content, section_page_id)
                        
                        if page_id:
                            print(f"Successfully imported: {page_name}")
                        else:
                            print(f"Failed to import: {page_name}")
                        
                        # Rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"Error processing file {md_file}: {str(e)}")

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        required_fields = ['notion_token', 'parent_page_id', 'root_folder', 'imgbb_key']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            print(f"Missing required fields in config.json: {', '.join(missing_fields)}")
            print("Please update config.json with your settings.")
            return None
            
        return config
    except FileNotFoundError:
        print("config.json not found. Please create it with your settings.")
        return None
    except json.JSONDecodeError:
        print("Error reading config.json. Please check the format.")
        return None

def validate_token(token):
    """Validate the Notion API token by attempting to list users"""
    try:
        client = Client(auth=token)
        client.users.list()
        return True
    except Exception as e:
        print(f"Error validating token: {str(e)}")
        return False

def main():
    print("Welcome to Notion Markdown Importer!")
    print("------------------------------------")
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Validate the token
    if not validate_token(config['notion_token']):
        print("Invalid Notion API token in config.json. Please check your integration token.")
        return
    
    # Convert backslashes to forward slashes in path
    root_folder = config['root_folder'].replace("\\", "/")
    
    # Validate the root folder
    if not os.path.exists(root_folder):
        print(f"Error: The folder path '{root_folder}' does not exist.")
        return
    
    # Initialize importer
    importer = NotionImporter(config['notion_token'], config['parent_page_id'], config['imgbb_key'])
    
    print("\nStarting import process...")
    # Start import
    importer.import_structure(root_folder)
    print("\nImport process completed!")

if __name__ == "__main__":
    main()
