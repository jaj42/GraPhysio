from .feet_time_interval import get_feet_time_interval
from .feet_to_curve import get_feet_to_curve
from .perfusion_index import get_perfusion_index
from .precise_feet import get_precise_feet
from .pulse_transit import get_pat, get_tt
from .curve_to_feet import get_curve_to_feet

Transformations = {
    "Precise POIs": get_precise_feet,
    "POIs to Curve": get_feet_to_curve,
    "Perfusion Index": get_perfusion_index,
    "Pulse Arrival Time": get_pat,
    "Pulse Transit Time": get_tt,
    "POIs Time Interval": get_feet_time_interval,
    "Curve to POIs": get_curve_to_feet,
}
