"""Demo routes showcasing full application flow with Prometheus metrics."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
# Import metrics from the services directly
from app.services.user_service import USER_OPERATIONS, USER_DATABASE_QUERIES
from app.services.order_service import ORDER_OPERATIONS, ORDER_OPERATION_DURATION
from app.services.payment_service import PAYMENT_OPERATIONS, PAYMENT_OPERATION_DURATION

router = APIRouter()

# Initialize services
user_service = UserService()
order_service = OrderService()
payment_service = PaymentService()


@router.get("/full-flow/{user_id}")
async def demo_full_flow(user_id: int) -> Dict[str, Any]:
    """
    Demonstrate a complete application flow:
    1. Get user information
    2. Create an order
    3. Process payment
    
    This endpoint showcases distributed operations across all services
    with comprehensive Prometheus metrics collection.
    """
    try:
        # Step 1: Get user information
        try:
            user = await user_service.get_user(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Step 2: Create order for the user
        order_data = {
            "user_id": user_id,
            "amount": 99.99,
            "items": ["premium_item_1", "premium_item_2", "bonus_item"],
            "type": "express"
        }
        
        with ORDER_OPERATION_DURATION.labels(operation="create_order").time():
            order = await order_service.create_order(order_data)

        # Step 3: Process payment for the order
        payment_data = {
            "order_id": order["id"],
            "amount": order["amount"],
            "method": "credit_card"
        }
        
        payment = await payment_service.process_payment(payment_data)

        # Step 4: Process the order (move to processing status)
        processed_order = await order_service.process_order(order["id"])

        # Record business metrics for the successful flow
        USER_OPERATIONS.labels(operation="demo_flow", status="success").inc()  # Record successful demo flow
        USER_DATABASE_QUERIES.labels(query_type="get", status="success").inc()

        return {
            "flow_status": "completed",
            "user": user,
            "order": processed_order,
            "payment": payment,
            "summary": {
                "user_id": user_id,
                "user_name": user["name"],
                "order_id": order["id"],
                "order_amount": order["amount"],
                "payment_id": payment["id"],
                "payment_status": payment["status"],
                "net_amount": payment["net_amount"],
                "processing_fee": payment["processing_fee"]
            }
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full flow failed: {str(e)}"
        )


@router.post("/simulate-user-journey")
async def simulate_user_journey() -> Dict[str, Any]:
    """
    Simulate a complete new user journey:
    1. Create a new user
    2. Create an order for that user
    3. Process payment
    4. Complete the order
    
    This demonstrates the full application lifecycle with metrics.
    """
    try:
        # Step 1: Create a new user
        import random
        user_data = {
            "name": f"Demo User {random.randint(1000, 9999)}",
            "email": f"demo{random.randint(1000, 9999)}@example.com",
            "status": "active"
        }
        
        user = await user_service.create_user(user_data)

        # Step 2: Create an order for the new user
        order_data = {
            "user_id": user["id"],
            "amount": random.uniform(25.99, 199.99),
            "items": [f"item_{i}" for i in range(1, random.randint(2, 6))],
            "type": random.choice(["standard", "express", "bulk"])
        }
        
        order = await order_service.create_order(order_data)

        # Step 3: Process payment
        payment_methods = ["credit_card", "debit_card", "paypal", "apple_pay"]
        payment_data = {
            "order_id": order["id"],
            "amount": order["amount"],
            "method": random.choice(payment_methods)
        }
        
        payment = await payment_service.process_payment(payment_data)

        # Step 4: Process and complete the order
        processed_order = await order_service.process_order(order["id"])
        completed_order = await order_service.update_order_status(
            order["id"], 
            "completed", 
            "order_fulfilled"
        )

        return {
            "journey_status": "completed",
            "steps_completed": 4,
            "user": user,
            "order": completed_order,
            "payment": payment,
            "metrics_recorded": {
                "user_created": True,
                "order_processed": True,
                "payment_completed": True,
                "order_completed": True
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User journey simulation failed: {str(e)}"
        )


@router.get("/stress-test")
async def stress_test_metrics() -> Dict[str, Any]:
    """
    Generate various operations to test metrics collection under load.
    This endpoint performs multiple operations to generate diverse metrics.
    """
    import random
    import asyncio
    
    results = {
        "operations_performed": [],
        "metrics_generated": True,
        "test_summary": {}
    }
    
    try:
        # Test user operations
        user_ops = []
        for i in range(3):
            try:
                # Try to get random users
                user_id = random.randint(1, 10)
                user = await user_service.get_user(user_id)
                user_ops.append(f"Retrieved user {user_id}")
            except:
                user_ops.append(f"User {user_id} not found (expected)")
        
        results["operations_performed"].extend(user_ops)

        # Test order operations
        order_ops = []
        for i in range(2):
            try:
                order_id = random.randint(100, 200)
                order = await order_service.get_order(order_id)
                order_ops.append(f"Retrieved order {order_id}")
            except:
                order_ops.append(f"Order {order_id} not found (expected)")
        
        results["operations_performed"].extend(order_ops)

        # Test payment operations
        payment_ops = []
        for i in range(2):
            try:
                payment_id = random.randint(1000, 2000)
                payment = await payment_service.get_payment(payment_id)
                payment_ops.append(f"Retrieved payment {payment_id}")
            except:
                payment_ops.append(f"Payment {payment_id} not found (expected)")
        
        results["operations_performed"].extend(payment_ops)

        # Generate some database query operations for metrics
        for _ in range(5):
            query_status = random.choice(["success", "error"])
            USER_DATABASE_QUERIES.labels(query_type="get", status=query_status).inc()

        results["test_summary"] = {
            "total_operations": len(results["operations_performed"]),
            "user_operations": len(user_ops),
            "order_operations": len(order_ops),
            "payment_operations": len(payment_ops),
            "database_queries": 5
        }

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stress test failed: {str(e)}"
        )