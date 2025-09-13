#!/usr/bin/env python3
"""
Passenger Modeler v1.2.0
========================

Interactive passenger model generator using statistical plugins.
"""

import sys
import json
import argparse
from typing import Any, Dict
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from utils import ConfigManager, PluginLoader

# Version constant - must match config.ini [version] section
PASSENGER_MODELER_VERSION = "1.2.0"

def check_version_compatibility(config_manager):
    """Check if passenger_modeler version matches config.ini version"""
    try:
        config_version = config_manager.get_version()
        if config_version != PASSENGER_MODELER_VERSION:
            print(f"VERSION MISMATCH!")
            print(f"   Config version: {config_version}")
            print(f"   Script version: {PASSENGER_MODELER_VERSION}")
            print(f"   Please update the config.ini or passenger_modeler.py to match versions")
            return False
        
        print(f"Version check passed: {PASSENGER_MODELER_VERSION}")
        return True
        
    except Exception as e:
        print(f"Warning: Could not verify version compatibility: {e}")
        print(f"Continuing with script version: {PASSENGER_MODELER_VERSION}")
        return True


def _summarize_hourly_breakdown(hourly_breakdown: Dict[str, Any]):
    """Create a compact summary for large hourly breakdown sections"""
    try:
        hours = list(hourly_breakdown.items())
        if not hours:
            return {}
        # Extract expected_passengers where available
        ep_values = [(h, v.get('expected_passengers')) for h, v in hours if isinstance(v, dict) and 'expected_passengers' in v]
        if ep_values:
            sorted_by_load = sorted(ep_values, key=lambda x: x[1], reverse=True)
            avg = sum(v for _, v in ep_values) / len(ep_values)
            peak = sorted_by_load[0]
            low = sorted_by_load[-1]
            top3 = sorted_by_load[:3]
            return {
                'average_expected': round(avg, 2),
                'peak_hour': peak[0],
                'peak_expected': round(peak[1], 2),
                'quiet_hour': low[0],
                'quiet_expected': round(low[1], 2),
                'top_3_hours': [{h: round(v,2)} for h, v in top3]
            }
        # Fallback just count keys
        return {'hours_listed': len(hours)}
    except Exception:
        return {'summary_error': 'Could not summarize hourly_breakdown'}


def _pretty_print_stats(stats: Dict[str, Any], indent: int = 0, max_depth: int = 4, current_depth: int = 0):
    """Recursively pretty-print statistics with readable formatting.

    Special handling for known large sections like hourly_breakdown to avoid overwhelming output.
    """
    IND = ' ' * indent
    if not isinstance(stats, dict):
        print(f"{IND}{stats}")
        return
    import textwrap
    for key, value in stats.items():
        key_label = key.replace('_', ' ').title()
        # Special inline contextualization for top-level percentile/lambda style keys
        if key.lower() == 'lambda' and isinstance(value, (int, float)):
            print(f"{IND}Average Hourly Arrival Rate: {value} (this is the typical number of passengers arriving each hour)")
            continue
        if key.lower() == 'percentiles' and isinstance(value, dict):
            # Build contextual sentence
            p10 = value.get('10th') or value.get('10')
            p50 = value.get('50th') or value.get('50')
            p75 = value.get('75th') or value.get('75')
            p90 = value.get('90th') or value.get('90')
            p95 = value.get('95th') or value.get('95')
            expl_parts = []
            if p50 is not None:
                expl_parts.append(f"half of hours have {p50} or fewer")
            if p10 is not None and p90 is not None:
                expl_parts.append(f"typical range {p10}-{p90}")
            if p95 is not None:
                expl_parts.append(f"rarely above {p95} (about 1 in 20 hours)")
            sentence = ", ".join(expl_parts) + "." if expl_parts else "Distribution summary unavailable."
            print(f"{IND}Passenger Count Ranges: {sentence}")
            continue
        if isinstance(value, dict):
            # Special case large hourly breakdown
            if key == 'hourly_breakdown':
                summary = _summarize_hourly_breakdown(value)
                print(f"{IND}{key_label} (summary):")
                for sk, sv in summary.items():
                    print(f"{IND}  - {sk.replace('_',' ').title()}: {sv}")
                continue
            # Recognize possibly very deep sections and show only top-level keys
            if len(value) > 25 and current_depth >= 1:
                print(f"{IND}{key_label}: ({len(value)} keys - truncated list)")
                shown_keys = list(value.keys())[:15]
                for sk in shown_keys:
                    print(f"{IND}  - {sk}")
                remaining = len(value) - len(shown_keys)
                if remaining > 0:
                    print(f"{IND}  ... {remaining} more keys (use --max-depth {max_depth+2} to expand)")
                continue
            print(f"{IND}{key_label}:")
            if current_depth >= max_depth:
                print(f"{IND}  (nested data truncated at depth {max_depth})")
                continue
            _pretty_print_stats(value, indent=indent + 2, max_depth=max_depth, current_depth=current_depth + 1)
        elif isinstance(value, list):
            print(f"{IND}{key_label}:")
            if not value:
                print(f"{IND}  (empty)")
                continue
            # Print first few elements only
            preview = value[:5]
            for item in preview:
                if isinstance(item, (dict, list)):
                    print(f"{IND}  - {json.dumps(item)[:120]}" + ("..." if len(json.dumps(item)) > 120 else ""))
                else:
                    print(f"{IND}  - {item}")
            if len(value) > len(preview):
                print(f"{IND}  ... ({len(value)-len(preview)} more)")
        else:
            # Wrap long text values
            if isinstance(value, str) and len(value) > 100:
                wrapped = textwrap.wrap(value, width=100)
                print(f"{IND}{key_label}: {wrapped[0]}")
                for cont in wrapped[1:]:
                    print(f"{IND}{' '* (len(key_label)+2)}{cont}")
            else:
                print(f"{IND}{key_label}: {value}")


def _display_model_statistics(model_path: Path, show_raw: bool = False, max_depth: int = 4, export_md: Path | None = None) -> int:
    """Load a generated model JSON file and display passenger statistics."""
    if not model_path.exists():
        print(f"Model file not found: {model_path}")
        return 1
    try:
        with open(model_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return 1
    except Exception as e:
        print(f"Error reading file: {e}")
        return 1

    meta = data.get('metadata', {})
    print(f"Passenger Model Statistics Viewer v{PASSENGER_MODELER_VERSION}")
    print("=" * 60)
    print(f"File: {model_path}")
    if meta:
        print(f"Model Name: {meta.get('name', 'N/A')} | Type: {meta.get('model_type', 'unknown')} | Generated: {meta.get('generated_at', 'N/A')}")
    print("=" * 60)

    stats = data.get('statistics')
    if not stats:
        print("No 'statistics' section found in this model.\nAttempting minimal derived summary...")
        derived = {}
        params = data.get('model_info', {}).get('parameters') or {}
        if params:
            derived['parameter_keys'] = list(params.keys())
        locations = data.get('locations') or data.get('stops')
        if locations and isinstance(locations, list):
            derived['locations_count'] = len(locations)
        if not derived:
            print("Could not derive any statistics from legacy model structure.")
            return 0
        print(json.dumps(derived, indent=2))
        return 0

    # Plain language context before raw structured stats
    # Capture narrative for optional export
    from io import StringIO
    narrative_buffer = StringIO()
    _print_plain_language(stats)
    # Re-run narrative into buffer for export if needed
    if export_md:
        # Temporarily redirect stdout for narrative capture
        import contextlib, sys as _sys
        tmp_buf = StringIO()
        with contextlib.redirect_stdout(tmp_buf):
            _print_plain_language(stats)
        narrative_text = tmp_buf.getvalue()
    else:
        narrative_text = ''

    raw_buffer = ''
    if show_raw:
        print("\n--- Technical Details (requested with --raw) ---")
        # Capture raw details if exporting
        if export_md:
            import contextlib, sys as _sys
            raw_tmp = StringIO()
            with contextlib.redirect_stdout(raw_tmp):
                _pretty_print_stats(stats, max_depth=max_depth)
            raw_buffer = raw_tmp.getvalue()
            # Also print to console separately
            _pretty_print_stats(stats, max_depth=max_depth)
        else:
            _pretty_print_stats(stats, max_depth=max_depth)

    if export_md:
        md_lines = [
            f"# Passenger Model Statistics", "",
            f"**File:** `{model_path}`  ",
            f"**Generated:** {meta.get('generated_at', 'N/A')}  ",
            f"**Model Type:** {meta.get('model_type','unknown')}  ",
            f"**Viewer Version:** {PASSENGER_MODELER_VERSION}",
            "",
            "## Plain Language Summary", "",
            '```',
            narrative_text.strip(),
            '```'
        ]
        if show_raw:
            md_lines += [
                "\n## Technical Details", "",
                '```',
                raw_buffer.strip(),
                '```'
            ]
        try:
            export_md.parent.mkdir(parents=True, exist_ok=True)
            export_md.write_text("\n".join(md_lines), encoding='utf-8')
            print(f"\nMarkdown export written to: {export_md}")
        except Exception as e:
            print(f"Failed to write markdown export: {e}")

    print("\nDone.")
    return 0


def _print_plain_language(stats: Dict[str, Any]):
    """Print a layman-friendly narrative explaining key statistics."""
    try:
        print("\nPassenger Demand Summary (Plain Language)")

        # Mean / average
        mean = None
        std = None
        lambda_val = None
        percentiles = None

        # Flexible extraction for both poisson & gaussian style keys
        for k in ['mean_passengers_per_hour', 'mean']:
            if k in stats and isinstance(stats[k], (int, float)):
                mean = stats[k]
                break
        for k in ['std_dev', 'std']:
            if k in stats and isinstance(stats[k], (int, float)):
                std = stats[k]
                break
        if 'lambda' in stats:
            lambda_val = stats['lambda']
        if 'percentiles' in stats and isinstance(stats['percentiles'], dict):
            percentiles = stats['percentiles']

        if mean is not None:
            print(f"On a typical hour, you can expect about {round(mean,2)} passengers.")
        if std is not None and mean:
            cv = std/mean if mean else 0
            variability = (
                'very consistent' if cv < 0.15 else
                'fairly predictable' if cv < 0.30 else
                'moderately variable' if cv < 0.50 else
                'quite variable'
            )
            print(f"Variation: The numbers usually fluctuate by about ±{round(std,2)} passengers, which means demand is {variability}.")
        if lambda_val is not None:
            print(f"Rate (λ): '{lambda_val}' is the average number of passenger arrivals per hour the model is built around.")
            print("Think of λ as: if you watched for many hours, this is the typical count you'd see each hour on average.")
        if percentiles:
            # Pick some common ones
            p50 = percentiles.get('50th')
            p10 = percentiles.get('10th') or percentiles.get('10')
            p90 = percentiles.get('90th') or percentiles.get('90')
            p95 = percentiles.get('95th') or percentiles.get('95')
            parts = []
            if p50 is not None:
                parts.append(f"Half of all hours have {p50} passengers or fewer (that's the median)")
            if p10 is not None and p90 is not None:
                parts.append(f"In quiet times you might see as few as {p10}; in busy times up to about {p90} per hour")
            if p95 is not None:
                parts.append(f"Only about 1 in 20 hours will go above {p95} passengers")
            if parts:
                print("Percentiles explained: " + "; ".join(parts) + ".")
            print("A 'percentile' just tells you how unusual a value is. For example the 90th percentile means only 1 out of 10 hours will be higher than that number.")

        # Capacity hint if present
        cap_planning = stats.get('capacity_planning') or stats.get('service_recommendations')
        if isinstance(cap_planning, dict):
            if 'peak_capacity' in cap_planning:
                pc = cap_planning.get('peak_capacity')
                if isinstance(pc, (int, float)):
                    print(f"Planning Hint: You should be prepared for peak hours reaching around {pc} passengers.")
            elif 'vehicle_capacity' in cap_planning:
                vcap = cap_planning['vehicle_capacity']
                if isinstance(vcap, dict) and 'optimal_capacity' in vcap:
                    print(f"Recommended vehicle capacity: about {vcap['optimal_capacity']} seats to handle busy periods with a safety margin.")
        # Tuning guidance AFTER showing current interpretation
        print("\nHow To Adjust These Numbers:")
        print("  • Increase overall passengers:")
        print("      - Poisson model: raise 'base_lambda' in the Poisson plugin config (plugins/configs/*poisson*.ini/json).")
        print("      - Gaussian model: raise 'base_mean' (or 'mean_passengers').")
        print("  • Make peaks higher (rush hours busier): increase multipliers in time pattern sections (e.g. evening_commute multiplier 2.0 → 2.5).")
        print("  • Spread demand more evenly: reduce extreme multipliers (e.g. 2.5 → 1.8) and raise low periods (0.5 → 0.8).")
        print("  • Boost specific locations: raise amenity weights (e.g. 'school'=8 → 12) for places you want to generate more riders near.")
        print("  • Reduce variability:")
        print("      - Poisson: variability is tied to the mean; use lower multipliers or lower base_lambda.")
        print("      - Gaussian: lower 'base_std' (or 'std_passengers').")
        print("  • Create stronger difference between quiet and busy times: widen the gap between low and high time pattern multipliers.")
        print("  • Capacity planning after changes: regenerate the model and view again to see updated peak expectations.")
        print("  (Plugin config files are in passenger_modeler/plugins/configs/. Edit then re-run generation.)")

        print("-" * 60)
    except Exception as e:
        print(f"(Could not generate plain-language summary: {e})")

def main():
    """Main entry point supporting two modes: generation (default) and statistics viewing."""

    parser = argparse.ArgumentParser(
        description="Passenger Modeler - generate models or display statistics from existing model JSON files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--model-file', '-m', metavar='PATH', help='Display passenger statistics (plain-English by default) from an existing model JSON and exit')
    parser.add_argument('--raw', action='store_true', help='Include full technical/statistical detail')
    parser.add_argument('--export-md', metavar='PATH', help='Export the plain-English (and optional raw with --raw) statistics to a Markdown file')
    parser.add_argument('--max-depth', type=int, default=4, help='Max depth for nested statistics printing when --raw is used')
    parser.add_argument('--version', action='store_true', help='Show version and exit')
    args = parser.parse_args()

    if args.version:
        print(f"Passenger Modeler v{PASSENGER_MODELER_VERSION}")
        return 0

    # Statistics viewing mode
    if args.model_file:
        export_path = Path(args.export_md) if args.export_md else None
        return _display_model_statistics(Path(args.model_file), show_raw=args.raw, max_depth=args.max_depth, export_md=export_path)

    print(f"Passenger Modeler v{PASSENGER_MODELER_VERSION}")
    print("Interactive Statistical Model Generator")
    print("="*50)
    
    # Load configuration first to check version
    config_path = Path(__file__).parent / 'config.ini'
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return 1
    
    try:
        config_manager = ConfigManager(str(config_path))
        print("Configuration loaded")
        
        # Check version compatibility
        if not check_version_compatibility(config_manager):
            return 1
        
        default_model = config_manager.get_model_type()
        print(f"Default model from config: {default_model}")
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return 1
    

    # Initialize plugin system
    current_dir = Path(__file__).parent
    plugins_dir = current_dir / 'plugins'
    configs_dir = plugins_dir / 'configs'  # Configs now inside plugins folder

    try:
        plugin_loader = PluginLoader(str(plugins_dir), str(configs_dir), config_manager)
        print(f"Loaded {len(plugin_loader.get_available_models())} statistical models")
    except Exception as e:
        print(f"Failed to initialize plugin system: {e}")
        return 1

    # Verify default model is available
    available_models = plugin_loader.get_available_models()
    if default_model not in available_models:
        print(f"Warning: Default model '{default_model}' not available")
        print(f"Available models: {', '.join(available_models)}")
        default_model = available_models[0] if available_models else 'poisson'

    # Interactive model selection
    def select_model(plugin_loader, default_model):
        models_info = plugin_loader.list_models_with_details()
        model_types = list(models_info.keys())
        print("\nAvailable Statistical Models:")
        print("=" * 40)
        for i, (model_type, info) in enumerate(models_info.items(), 1):
            default_marker = " (default)" if model_type == default_model else ""
            print(f"{i}. {model_type.upper()}{default_marker}")
            print(f"   {info.get('name', 'Unknown Model')}")
            print(f"   {info.get('amenity_types_count', 0)} amenity types, {info.get('time_patterns_count', 0)} time patterns")
            print()
        while True:
            try:
                choice = input(f"Select model (1-{len(model_types)}) [default: {default_model}]: ").strip()
                if not choice:
                    return default_model
                choice_num = int(choice)
                if 1 <= choice_num <= len(model_types):
                    return model_types[choice_num - 1]
                else:
                    print(f"Please enter a number between 1 and {len(model_types)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nCancelled")
                return None

    def get_output_name():
        while True:
            output_name = input("Enter output model name (without .json): ").strip()
            if not output_name:
                print("Please enter a model name")
                continue
            safe_name = "".join(c for c in output_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            if not safe_name:
                print("Please enter a valid model name")
                continue
            return safe_name

    selected_model = select_model(plugin_loader, default_model)
    if not selected_model:
        return 0  # User cancelled

    output_name = get_output_name()

    # Generate the model
    try:
        print(f"\nGenerating {selected_model.upper()} model...")
        model = plugin_loader.create_model(selected_model)
        if not model:
            print(f"Failed to create {selected_model} model")
            return 1
        print(f"Created {selected_model} statistical model")

        generated_model = {
            "metadata": {
                "name": output_name,
                "model_type": selected_model,
                "generated_at": datetime.now().isoformat(),
                "version": PASSENGER_MODELER_VERSION,
                "config_version": config_manager.get_version()
            },
            "config": config_manager.get_config_dict(),
            "model_info": {
                "parameters": getattr(model, 'config', {})
            },
            "statistics": model.get_distribution_statistics(),
            "note": "This is a placeholder - GeoJSON processing integration needed"
        }

        output_dir = Path(__file__).parent / "models" / "generated"
        output_file = output_dir / f"{output_name}.json"
        with open(output_file, 'w') as f:
            json.dump(generated_model, f, indent=2)
        print(f"Model saved to: {output_file}")
        print(f"Model type: {selected_model.upper()}")
        print(f"Output: {output_name}.json")
        print(f"Generator version: {PASSENGER_MODELER_VERSION}")
        print("\nModel generation completed successfully!")
        return 0
    except Exception as e:
        print(f"Error generating model: {e}")
        print("\nModel generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
