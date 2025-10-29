def get_client_ip(request):
	"""
	Return the best-guess client IP address.
	Handles X-Forwarded-For and X-Real-IP headers.
	"""
	xff = request.META.get("HTTP_X_FORWARDED_FOR")
	if xff:
		ip = xff.split(",")[0].strip()
	else:
		ip = request.META.get("HTTP_X_REAL_IP")
	if not ip:
		ip = request.META.get("REMOTE_ADDR")
	return ip