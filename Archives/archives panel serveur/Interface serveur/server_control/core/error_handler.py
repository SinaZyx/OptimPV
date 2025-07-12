import os
import tempfile
from datetime import datetime

# Tentative d'import du logger global, sinon fallback print
try:
    from optimpv_main import logger as global_logger
    # Pour s'assurer qu'on a bien une méthode write, comme le logger simple
    if not hasattr(global_logger, 'write'):
        # Si le logger global n'a pas de 'write', on encapsule ou on utilise un logger local
        class LoggerWrapper:
            def __init__(self, logger_instance):
                self.logger_instance = logger_instance
            def write(self, msg, level="ERROR"):
                if hasattr(self.logger_instance, level.lower()):
                    getattr(self.logger_instance, level.lower())(msg)
                elif hasattr(self.logger_instance, 'error'): # Fallback sur error()
                    self.logger_instance.error(f"[{level}] {msg}")
                else: # Fallback sur print
                    print(f"LoggerWrapper [{level}]: {msg}")
        logger = LoggerWrapper(global_logger)
        logger.write("ErrorHandler: Wrapped global_logger to ensure write method.", level="INFO")
    else:
        logger = global_logger
        logger.write("ErrorHandler: Using global_logger from optimpv_main.", level="INFO")
except (ImportError, ModuleNotFoundError):
    # En cas d'échec (ex: tests unitaires, ou si ce module est chargé avant optimpv_main.logger)
    # On crée un logger basique pour ce module.
    class FallbackErrorHandlerLogger:
        def __init__(self, filepath):
            self.filepath = filepath
            self._log(f"=== FallbackErrorHandlerLogger Initialized ({datetime.now()}) ===", "INFO")

        def _log(self, msg, level):
            formatted_msg = f"[{level}] {datetime.now()}: {msg}"
            print(formatted_msg) # Sortie console
            try:
                with open(self.filepath, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_msg}\n")
                    f.flush()
            except Exception as e:
                print(f"FallbackErrorHandlerLogger: Failed to write to log file {self.filepath}: {e}")
        
        # Méthode `write` pour compatibilité avec le logger SimpleLogger
        def write(self, msg, level="ERROR"): # Par défaut à ERROR car c'est un error handler
            self._log(msg, level)
            
    temp_log_file_path = os.path.join(tempfile.gettempdir(), f"errorhandler_fallback_{os.getpid()}.log")
    logger = FallbackErrorHandlerLogger(temp_log_file_path)
    logger.write("ErrorHandler: Global logger from optimpv_main not found. Using FallbackErrorHandlerLogger.", level="INFO")

class ErrorHandler:
    """Gestionnaire centralisé des erreurs avec fallback."""
    
    _error_log_file = os.path.join(tempfile.gettempdir(), "optimpv_critical_errors.log")

    @staticmethod
    def _log_critical_error(func_name: str, exception: Exception):
        """Loggue une erreur critique dans un fichier de secours dédié."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_message = f"{timestamp}: CRITICAL ERROR in {func_name} - {type(exception).__name__}: {str(exception)}\n"
        # Optionnel: ajouter le traceback
        # import traceback
        # error_message += traceback.format_exc() + "\n"
        try:
            with open(ErrorHandler._error_log_file, "a", encoding='utf-8') as f:
                f.write(error_message)
                f.flush()
            # Tenter de logger aussi avec le logger principal/fallback du module
            logger.write(f"Critical error logged to {ErrorHandler._error_log_file}: In {func_name} - {str(exception)}", level="ERROR")
        except Exception as log_e:
            # Si même le logging de secours échoue, on print en dernier recours
            print(f"ULTIMATE FALLBACK: Failed to write to critical error log. Original error in {func_name}: {str(exception)}. Logging error: {log_e}")
            print(error_message) # Afficher le message d'erreur original

    @staticmethod
    def safe_execute(func, fallback_return_value_factory=None, log_errors=True, raise_on_failure=False):
        """Exécute une fonction avec gestion d'erreur.

        Args:
            func (Callable): La fonction à exécuter.
            fallback_return_value_factory (Callable, optional): Une fonction qui retourne une valeur de fallback en cas d'erreur.
                                                              Si None, l'erreur est levée (sauf si raise_on_failure est False).
            log_errors (bool): Si True, loggue l'erreur en utilisant le logger du module et le fichier critique.
            raise_on_failure (bool): Si True et fallback_return_value_factory est None, lève l'exception après l'avoir logguée.
                                     Si False et fallback_return_value_factory est None, retourne None en cas d'erreur.

        Returns:
            La valeur de retour de la fonction, ou la valeur de fallback, ou None.

        Raises:
            L'exception originale si fallback_return_value_factory est None et raise_on_failure est True.
        """
        func_name = getattr(func, '__name__', 'anonymous_function')
        try:
            # logger.write(f"ErrorHandler: Safely executing {func_name}...", level="DEBUG") # Peut être verbeux
            return func()
        except Exception as e:
            logger.write(f"ErrorHandler: Exception caught in {func_name}: {type(e).__name__} - {e}", level="ERROR")
            if log_errors:
                ErrorHandler._log_critical_error(func_name, e)
            
            if fallback_return_value_factory is not None:
                logger.write(f"ErrorHandler: Executing fallback for {func_name}.", level="WARNING")
                try:
                    return fallback_return_value_factory()
                except Exception as fb_e:
                    logger.write(f"ErrorHandler: Exception in fallback for {func_name}: {type(fb_e).__name__} - {fb_e}", level="ERROR")
                    ErrorHandler._log_critical_error(f"{func_name} (fallback)", fb_e)
                    if raise_on_failure: # Si le fallback lui-même échoue et qu'on doit lever
                        raise fb_e from e # Lève l'erreur du fallback, enchaînée à l'originale
                    return None # Ou retourne None si le fallback échoue et qu'on ne doit pas lever
            
            if raise_on_failure:
                logger.write(f"ErrorHandler: Re-raising exception from {func_name}.", level="ERROR")
                raise
            
            # Si pas de fallback et raise_on_failure est False, on retourne None
            logger.write(f"ErrorHandler: Suppressed exception from {func_name}, returning None.", level="WARNING")
            return None

# Exemple d'utilisation
if __name__ == "__main__":
    logger.write("\n--- Testing ErrorHandler --- ", level="INFO")

    def might_fail_division(a, b):
        logger.write(f"Executing might_fail_division({a}, {b})", level="INFO")
        return a / b

    def fallback_for_division():
        logger.write("Executing fallback_for_division, returning 0", level="INFO")
        return 0
        
    def fallback_that_fails():
        logger.write("Executing fallback_that_fails... and it will fail!", level="INFO")
        raise ValueError("Fallback itself failed!")

    # Test 1: Succès
    result = ErrorHandler.safe_execute(lambda: might_fail_division(10, 2))
    logger.write(f"Test 1 (Success): Result = {result}\n", level="INFO")

    # Test 2: Échec, avec fallback qui retourne une valeur
    result = ErrorHandler.safe_execute(
        lambda: might_fail_division(10, 0),
        fallback_return_value_factory=fallback_for_division
    )
    logger.write(f"Test 2 (Failure with fallback): Result = {result}\n", level="INFO")

    # Test 3: Échec, sans fallback, raise_on_failure=False (défaut pour fallback=None implicite)
    # (Note: la logique actuelle retourne None si fallback_return_value_factory est None et raise_on_failure est False)
    result = ErrorHandler.safe_execute(lambda: might_fail_division(5, 0))
    logger.write(f"Test 3 (Failure, no fallback, default no raise): Result = {result}\n", level="INFO")

    # Test 4: Échec, sans fallback explicite, mais avec raise_on_failure=True
    try:
        ErrorHandler.safe_execute(
            lambda: might_fail_division(10, 0),
            raise_on_failure=True
        )
    except ZeroDivisionError as e:
        logger.write(f"Test 4 (Failure, no fallback, raise_on_failure=True): Caught expected error: {e}\n", level="INFO")
        
    # Test 5: Échec, avec un fallback qui lui-même échoue, sans raise_on_failure pour le fallback
    result = ErrorHandler.safe_execute(
        lambda: might_fail_division(10,0),
        fallback_return_value_factory=fallback_that_fails
    )
    logger.write(f"Test 5 (Failure, fallback also fails, no raise from fallback): Result = {result}\n", level="INFO")

    # Test 6: Échec, avec un fallback qui lui-même échoue, ET raise_on_failure=True pour le fallback
    try:
        ErrorHandler.safe_execute(
            lambda: might_fail_division(10,0),
            fallback_return_value_factory=fallback_that_fails,
            raise_on_failure=True # S'applique si le fallback échoue
        )
    except ValueError as e:
         logger.write(f"Test 6 (Failure, fallback also fails, raise_on_failure=True from fallback): Caught expected error from fallback: {e}\n", level="INFO")

    logger.write(f"Critical errors (if any) were logged to: {ErrorHandler._error_log_file}", level="INFO") 