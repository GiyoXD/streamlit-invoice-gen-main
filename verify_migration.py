
import sys
import os
import logging
import types
from decimal import Decimal
from unittest.mock import MagicMock
import importlib.util

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.abspath("src"))

# --- Mock Package Structure ---
# Create mock invoice_generator package structure
invoice_generator = types.ModuleType("invoice_generator")
invoice_generator.styling = types.ModuleType("invoice_generator.styling")
invoice_generator.styling.models = types.ModuleType("invoice_generator.styling.models")
invoice_generator.data = types.ModuleType("invoice_generator.data")
invoice_generator.config = types.ModuleType("invoice_generator.config")

# Mock FooterData
class MockFooterData:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
invoice_generator.styling.models.FooterData = MockFooterData

# Inject into sys.modules
sys.modules["invoice_generator"] = invoice_generator
sys.modules["invoice_generator.styling"] = invoice_generator.styling
sys.modules["invoice_generator.styling.models"] = invoice_generator.styling.models
sys.modules["invoice_generator.data"] = invoice_generator.data
sys.modules["invoice_generator.config"] = invoice_generator.config

# Mock invoice_generator.data.data_preparer
data_preparer = types.ModuleType("invoice_generator.data.data_preparer")
data_preparer.prepare_data_rows = MagicMock(return_value=([], [], False, 0))
data_preparer.parse_mapping_rules = MagicMock(return_value={
    'col1_index': 0, 'num_static_labels': 0, 'initial_static_col1_values': [],
    'static_column_header_name': '', 'apply_special_border_rule': False,
    'formula_rules': {}, 'dynamic_mapping_rules': {}, 'static_value_map': {}
})
data_preparer._to_numeric = MagicMock()
data_preparer._apply_fallback = MagicMock()
invoice_generator.data.data_preparer = data_preparer
sys.modules["invoice_generator.data.data_preparer"] = data_preparer

# Mock invoice_generator.utils.math_utils
invoice_generator.utils = types.ModuleType("invoice_generator.utils")
math_utils = types.ModuleType("invoice_generator.utils.math_utils")
def safe_float_convert(val):
    try: return float(val)
    except: return 0.0
def safe_int_convert(val):
    try: return int(float(val))
    except: return 0
math_utils.safe_float_convert = safe_float_convert
math_utils.safe_int_convert = safe_int_convert
invoice_generator.utils.math_utils = math_utils
sys.modules["invoice_generator.utils"] = invoice_generator.utils
sys.modules["invoice_generator.utils.math_utils"] = math_utils

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Load table_value_adapter (needed by builder_config_resolver)
    tva_path = os.path.abspath("src/invoice_generator/src/config/table_value_adapter.py")
    table_value_adapter = load_module("invoice_generator.config.table_value_adapter", tva_path)
    
    # Load builder_config_resolver
    bcr_path = os.path.abspath("src/invoice_generator/src/config/builder_config_resolver.py")
    builder_config_resolver = load_module("invoice_generator.config.builder_config_resolver", bcr_path)
    
    # Load table_calculator
    tc_path = os.path.abspath("src/invoice_generator/src/data/table_calculator.py")
    table_calculator = load_module("invoice_generator.data.table_calculator", tc_path)
    
    # Import data_processor (should work normally as src is in path)
    from data_parser import data_processor
    
except Exception as e:
    logger.error(f"Failed to load modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# --- Tests ---

def test_data_processor_summaries():
    print("Testing data_processor summaries...")
    
    # Mock data
    processed_data = {
        'description': ['BUFFALO LEATHER', 'COW LEATHER', 'BUFFALO SPLIT'],
        'pallet_count': ['10', '5', '2'],
        'net': ['100.5', '50.2', '20.1'],
        'gross': ['110.5', '55.2', '22.1'],
        'sqft': ['1000', '500', '200']
    }
    
    # Test Leather Summary
    leather_summary = data_processor.calculate_leather_summary(processed_data)
    print(f"Leather Summary: {leather_summary}")
    assert leather_summary['BUFFALO']['pallet_count'] == 12 # 10 + 2
    assert leather_summary['COW']['pallet_count'] == 5
    
    # Test Weight Summary
    weight_summary = data_processor.calculate_weight_summary(processed_data)
    print(f"Weight Summary: {weight_summary}")
    assert weight_summary['net'] == Decimal('170.8')
    assert weight_summary['gross'] == Decimal('187.8')
    
    # Test Pallet Summary
    pallet_summary = data_processor.calculate_pallet_summary(processed_data)
    print(f"Pallet Summary: {pallet_summary}")
    assert pallet_summary == 17

    print("[PASS] data_processor summaries passed!")

def test_builder_config_resolver_aggregation():
    print("\nTesting BuilderConfigResolver aggregation...")
    
    # Mock invoice_data with pre-calculated summaries
    invoice_data = {
        'processed_tables_data': {
            '1': {
                'weight_summary': {'net': Decimal('100'), 'gross': Decimal('110')},
                'pallet_summary_total': 10
            },
            '2': {
                'weight_summary': {'net': Decimal('50'), 'gross': Decimal('55')},
                'pallet_summary_total': 5
            }
        }
    }
    
    # Mock ConfigLoader
    mock_loader = MagicMock()
    mock_loader.get_sheet_config.return_value = {}
    mock_loader.get_raw_config.return_value = {}
    
    resolver = builder_config_resolver.BuilderConfigResolver(
        config_loader=mock_loader,
        sheet_name="TestSheet",
        worksheet=MagicMock(),
        invoice_data=invoice_data
    )
    
    context = resolver.get_context_bundle()
    print(f"Context Summaries: Net={context.get('total_net_weight')}, Gross={context.get('total_gross_weight')}, Pallets={context.get('total_pallets')}")
    
    assert context['total_net_weight'] == 150.0
    assert context['total_gross_weight'] == 165.0
    assert context['total_pallets'] == 15
    
    print("[PASS] BuilderConfigResolver aggregation passed!")

def test_table_calculator_usage():
    print("\nTesting TableCalculator usage...")
    
    # Mock resolved_data with pre-calculated summaries
    resolved_data = {
        'data_rows': [],
        'pallet_counts': [],
        'leather_summary': {'BUFFALO': {'pallet_count': 10}},
        'weight_summary': {'net': Decimal('100'), 'gross': Decimal('110')},
        'pallet_summary_total': 10
    }
    
    header_info = {'column_id_map': {}}
    calculator = table_calculator.TableCalculator(header_info)
    
    footer_data = calculator.calculate(resolved_data)
    
    print(f"FooterData: Pallets={footer_data.total_pallets}, Net={footer_data.weight_summary['net']}")
    
    assert footer_data.total_pallets == 10
    assert footer_data.weight_summary['net'] == Decimal('100')
    assert footer_data.leather_summary['BUFFALO']['pallet_count'] == 10
    
    print("[PASS] TableCalculator usage passed!")

if __name__ == "__main__":
    try:
        test_data_processor_summaries()
        test_builder_config_resolver_aggregation()
        test_table_calculator_usage()
        print("\n[SUCCESS] All verification tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Verification failed: {e}")
        # traceback.print_exc()
        sys.exit(1)
