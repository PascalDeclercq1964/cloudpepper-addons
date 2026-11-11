def post_init_hook(env):
    env["marketplace.field"]._ensure_flag_fields()
    env["marketplace.field"]._load_suggestions()
