#!/bin/bash

# Set the input directory where your markdown files are located
input_directory="."

# Iterate over all markdown files in the directory
for file in "$input_directory"/*.md; do
    # Initialize section number
    section_number=1

    # Create a temporary file to store the modified content
    tmp_file=$(mktemp)

    # Read each line of the original file
    while IFS= read -r line; do
        # Check if the line contains a URL
        if [[ $line =~ ^https:// ]]; then
            # Append a heading tag with the section number
            echo -e "\n## Section $section_number\n" >> "$tmp_file"
            # Increment the section number
            ((section_number++))
        fi
        # Append the current line to the temporary file
        echo "$line" >> "$tmp_file"
    done < "$file"

    # Overwrite the original file with the modified content
    mv "$tmp_file" "$file"
done

echo "Section numbers added to all markdown files in $input_directory."
