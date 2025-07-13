# Work Calculator

This script helps you calculate how much time went into a project using an extensible plugin architecture.

## Supported Data Sources

The system uses a plugin architecture that makes it easy to add new data sources:

- **Git**: Analyze commit timestamps from Git repositories
- **Logic**: Analyze bounce file timestamps from Logic Pro projects

## Adding New Data Sources

To add a new data source plugin:

1. Create a new plugin class that inherits from `DataSourcePlugin`
2. Implement all required abstract methods:
   - `source_name`: Unique identifier for your data source
   - `item_name`: Name for individual work items (e.g., "commit", "bounce", "task")
   - `help_text`: Short description for CLI help
   - `description`: Longer description for CLI help
   - `add_arguments()`: Add CLI arguments specific to your data source
   - `from_args()`: Create plugin instance from parsed arguments
   - `validate_source()`: Verify the data source is valid
   - `get_work_items()`: Yield WorkItem objects from your data source

3. Register your plugin in `plugins/__init__.py`:

   ```python
   PluginRegistry.register(YourDataSourcePlugin)
   ```

The system will automatically:

- Add your plugin to the CLI with appropriate subcommands
- Generate help text and examples
- Handle argument parsing and validation
- Use your plugin's `item_name` throughout the analysis

## Example Usage

```bash
# Analyze Git commits in the past 30 days
workcalc git /path/to/repo --since 30d

# Analyze Logic bounce files for 2024
workcalc logic /path/to/bounces --start 01/01/2024 --end 12/31/2024

# Any new plugins will automatically appear in --help
workcalc --help
```
