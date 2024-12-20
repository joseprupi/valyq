# core/services/logger_decorators.py
import functools
from typing import Any, Callable
from datetime import datetime
import inspect
from functools import wraps

def log_operation(operation_type: str):
    """Decorator for logging general operations"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Extract logger from self (assuming it's a service class)
            logger = self.logger

            # Get function parameters for logging
            params = inspect.signature(func).bind(self, *args, **kwargs)
            params.apply_defaults()
            # Remove 'self' from parameters
            log_params = dict(params.arguments)
            log_params.pop('self')

            # Create operation ID for tracking
            operation_id = f"{operation_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            try:
                # Log operation start
                logger.log_operation_start(
                    operation_type=operation_type,
                    operation_id=operation_id,
                    details=log_params
                )

                # Execute the function
                result = await func(self, *args, **kwargs)

                # Log operation success
                logger.log_operation_success(
                    operation_type=operation_type,
                    operation_id=operation_id,
                    result=result
                )

                return result

            except Exception as e:
                # Log operation failure
                logger.log_operation_error(
                    operation_type=operation_type,
                    operation_id=operation_id,
                    error=e,
                    details=log_params
                )
                raise

        return wrapper
    return decorator

# Specific decorators for common operations
def log_validation_operation(operation_name: str):
    """Decorator specifically for validation operations"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            logger = self.logger
            
            # Extract validation_id if present in args/kwargs
            validation_id = kwargs.get('validation_id')
            if not validation_id and args:
                # Assume first arg might be validation_id
                validation_id = args[0]

            try:
                logger.log_validation_event(
                    event_type=f"{operation_name}_started",
                    validation_id=validation_id or "unknown",
                    details={"args": str(args), "kwargs": str(kwargs)}
                )

                result = await func(self, *args, **kwargs)

                logger.log_validation_event(
                    event_type=f"{operation_name}_completed",
                    validation_id=validation_id or "unknown",
                    details={"result": str(result)}
                )

                return result

            except Exception as e:
                logger.log_validation_event(
                    event_type=f"{operation_name}_failed",
                    validation_id=validation_id or "unknown",
                    error=e
                )
                raise

        return wrapper
    return decorator

def log_llm_interaction(func: Callable):
    """Decorator for LLM interactions"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        logger = self.logger
        
        # Extract prompt from args or kwargs
        prompt = kwargs.get('prompt')
        if not prompt and args:
            prompt = args[0]

        try:
            # Log the prompt
            logger.log_llm_interaction(
                interaction_type="prompt",
                prompt=prompt,
                metadata=kwargs
            )

            result = await func(self, *args, **kwargs)

            # Log the response
            logger.log_llm_interaction(
                interaction_type="response",
                prompt=prompt,
                response=str(result),
                metadata=kwargs
            )

            return result

        except Exception as e:
            logger.log_llm_interaction(
                interaction_type="error",
                prompt=prompt,
                error=e,
                metadata=kwargs
            )
            raise

    return wrapper