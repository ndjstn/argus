
import typer
from main import ApplicationManager

app = typer.Typer()

@app.command()
def run():
    """
    Starts all services.
    """
    manager = ApplicationManager()
    manager.setup_signal_handlers()
    manager.start_all_services()

    # Keep the main thread alive to handle signals
    while not manager.shutdown_event.is_set():
        manager.shutdown_event.wait(timeout=1.0)

if __name__ == "__main__":
    app()
