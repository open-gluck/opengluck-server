from .userdata import get_userdata, set_userdata


def get_current_cgm_properties() -> dict:
    """Gets the current CGM device properties."""
    return {"has-real-time": do_we_have_realtime_cgm_data()}


def set_current_cgm_device_properties(properties: dict) -> None:
    """Sets the current CGM device properties."""
    set_userdata("cgm-current-device-properties", properties)


def do_we_have_realtime_cgm_data() -> bool:
    """Returns true if we have realtime CGM data.

    We suppose we always have CGM data, unless there is a
    `cgm-current-device-properties` userdata, set to an object with a
    `has-real-time` property set to false.
    """
    # LATER we should maybe have a proper endpoint for this
    cgm_current_device_properties = get_userdata("cgm-current-device-properties")
    if cgm_current_device_properties is None:
        return True
    return cgm_current_device_properties.get("has-real-time", True)
