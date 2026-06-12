from sqlmesh.core.context import Context

if __name__ == "__main__":
    print("🚀 Initializing SQLMesh Context via programmatic backdoor...")
    
    # Force initialize the project context directly from the local directory
    context = Context(paths=".")
    
    print("\n🔍 Evaluating model changes and generating deployment plan...")
    # Generate the execution plan programmatically
    plan = context.plan(
        environment="prod",
        no_prompts=True,   # Skips the CLI interactive prompt loop
        auto_apply=True    # Automatically builds the tables if validation passes
    )
    
    print("\n🎉 SQLMesh plan successfully applied to Supabase!")