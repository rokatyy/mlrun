import os
import argparse

def combine_docs(edition):
    # Paths to the content files
    shared_file = 'shared_contents.rst'
    community_file = 'community_contents.rst'
    enterprise_file = 'enterprise_contents.rst'
    output_file = 'contents.rst'

    # Open the output file for writing
    with open(output_file, 'w') as out_file:
        # Include shared content
        with open(shared_file, 'r') as shared:
            out_file.write(shared.read())

        # Include edition-specific content based on the 'edition' value
        if edition == 'community':
            with open(community_file, 'r') as community:
                out_file.write("\n\n" + community.read())
        elif edition == 'enterprise':
            with open(enterprise_file, 'r') as enterprise:
                out_file.write("\n\n" + enterprise.read())
        else:
            raise ValueError("Invalid edition specified. Use 'community' or 'enterprise'.")

    print(f"Combined documentation for {edition} edition into {output_file}")


# Set up command-line argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine shared and edition-specific docs.")
    parser.add_argument(
        '--edition',
        choices=['community', 'enterprise'],
        required=True,
        help="Specify the edition for the documentation (community or enterprise)"
    )

    args = parser.parse_args()
    combine_docs(args.edition)
