from .feet_to_curve import get_feet_to_curve
from .perfusion_index import get_perfusion_index
from .precise_feet import get_precise_feet

Transformations = {
    'Perfusion Index': get_perfusion_index,
    'Feet to Curve': get_feet_to_curve,
    'Precise Feet': get_precise_feet,
}
