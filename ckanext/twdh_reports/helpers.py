def reset_totp_from_template(username):
    try:
        from ckanext.security.authenticator import reset_totp
        reset_totp(username)
        return f"TOTP reset successful for {username}"
    except Exception as e:
        return f"TOTP reset failed: {str(e)}"