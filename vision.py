def estimate_meal(image_path: str, description: str | None = None) -> dict:
    """
    Fake meal estimator for MVP stage.

    Parameters
    ----------
    image_path : str
        Path to the downloaded food image.
    description : str | None
        Optional caption from the user.

    Returns
    -------
    dict
        Estimated meal data.
    """

    print("Vision module called")
    print("Image path:", image_path)
    print("Description:", description)

    # fake values for MVP testing
    return {
        "dish": "test meal",
        "calories": 500,
        "protein": 30
    }