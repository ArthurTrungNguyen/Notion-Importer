# Notion Markdown Importer

This script helps you import a structured collection of markdown files into Notion while maintaining their hierarchical organization. It now supports image uploads via ImgBB.

## Prerequisites

1. Python 3.7 or higher installed on your system
2. A Notion account
3. Your markdown files and resources organized in the correct structure

## Required Folder Structure

Your content should be organized as follows:
```
Root Folder (e.g., C:/Users/User/Downloads/OneNote)/
├── My Notebook/
│   ├── Section1/
│   │   ├── page1.md
│   │   └── page2.md
│   └── Section2/
│       └── page3.md
└── resources/
    ├── image1.png
    ├── image2.jpg
    └── other-images.png
```

## First-Time Setup

### 1. Install Required Dependencies

```bash
pip install notion-client markdown2 requests
```

### 2. Set Up Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name your integration (e.g., "Markdown Importer")
4. Select the workspace where you want to use the integration
5. Click "Submit" to create the integration
6. Copy the "Internal Integration Token"

### 3. Prepare Your Notion Workspace

1. Create a new page in Notion where you want to import your content
2. Click the "Share" button in the top right
3. Under "Add connections", find and select your integration
4. Get the page ID from the URL:
   - Example: For URL `https://www.notion.so/workspace/83c75a51b3774c2c8d5d42d55d1c23c4`
   - The page ID is `83c75a51b3774c2c8d5d42d55d1c23c4`

### 4. Get ImgBB API Key

1. Go to https://api.imgbb.com/
2. Create an account or log in if you already have one
3. Once logged in, go to your dashboard
4. Click on "Create API Key" or find your existing API key
5. Copy your API key for use in the configuration

### 5. Configure the Script

1. Open `config.json` in a text editor
2. Update the following values:
   ```json
   {
       "notion_token": "your_integration_token_here",
       "parent_page_id": "your_parent_page_id_here",
       "root_folder": "C:/Users/User/Downloads/OneNote",
       "imgbb_key": "your_imgbb_api_key_here"
   }
   ```
   - Replace `your_integration_token_here` with your Notion integration token
   - Replace `your_parent_page_id_here` with your destination page ID
   - Update `root_folder` with the path to your OneNote folder (use forward slashes)
   - Replace `your_imgbb_api_key_here` with the ImgBB API key you obtained in step 4

## Running the Script

Simply run:
```bash
python notion_import.py
```

The script will:
1. Load your configuration from config.json
2. Validate the Notion token and folder paths
3. Scan the resources folder for available images
4. Upload images to ImgBB
5. Create the notebook structure in Notion
6. Import all content with images

## Features

### Configuration Storage
- Saves your settings in config.json
- No need to enter tokens and paths each time
- Easy to update when needed

### Smart Image Handling
- Automatically finds images using multiple matching strategies
- Uploads images to ImgBB and uses the returned URLs in Notion
- Supports various image name formats
- Case-insensitive matching
- Detailed logging of image processing

### Content Organization
- Maintains your notebook structure
- Creates proper hierarchy in Notion
- Preserves markdown formatting
- Handles large content automatically

## Troubleshooting

### Common Issues and Solutions

1. "Config file not found":
   - Ensure config.json is in the same folder as the script
   - Check the JSON format is valid
   - Verify all required fields are present

2. "Invalid token":
   - Check your integration token in config.json
   - Verify the integration is still active
   - Ensure the token has proper permissions

3. "Folder not found":
   - Verify the path in config.json
   - Use forward slashes in paths
   - Check folder permissions

4. "Image not found":
   - Verify images are in the resources folder
   - Check image filenames match references
   - Look for case sensitivity issues

## Best Practices

1. Configuration:
   - Keep config.json secure
   - Use absolute paths
   - Use forward slashes in paths

2. Images:
   - Keep all images in the resources folder
   - Use consistent naming conventions
   - Verify image files exist before importing

3. Content:
   - Maintain the specified folder structure
   - Use clear, consistent naming
   - Keep paths free of special characters

## Security Notes

1. Never share your Notion integration token
2. Keep integration permissions limited to necessary pages
3. Revoke unused integration access
4. Monitor your integration usage

## Support

If you encounter issues:

1. Check the error messages in the terminal - they often provide specific guidance
2. Verify your integration settings at https://www.notion.so/my-integrations
3. Ensure your markdown files are properly formatted and encoded
4. Check Notion's API status at https://status.notion.so/

The script will maintain your complete notebook structure while properly handling both content and images, creating a fully functional Notion workspace that mirrors your original notebook organization.
