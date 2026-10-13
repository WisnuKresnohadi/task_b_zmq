
import os
import pickle
import sys
import zmq

from zmq.utils.monitor import recv_monitor_message

from messages import TaskMessage, ResultMessage


# 1. Read the worker's identity and result port.
if len(sys.argv) != 3:
    print("Usage: python worker.py <worker_id> <result_port>")
    raise SystemExit(1)

worker_id = sys.argv[1]
result_port = int(sys.argv[2])


# 2. Create the ZeroMQ context.
context = zmq.Context()

# 3. Read the distributor's hostname.
distributor_host = os.getenv(
    "DISTRIBUTOR_HOST",
    "127.0.0.1"
)

# 4. Create a PULL socket to receive tasks.
task_receiver = context.socket(zmq.PULL)

# Monitor the actual task connection.
task_monitor = task_receiver.get_monitor_socket(
    events=zmq.EVENT_HANDSHAKE_SUCCEEDED
)

task_receiver.connect(
    f"tcp://{distributor_host}:9921"
)

# 5. Create a PUSH socket to send results to the collector.
result_sender = context.socket(zmq.PUSH)
result_sender.bind(f"tcp://*:{result_port}")

# 6. Create a PUSH socket for readiness and completion messages.
ready_sender = context.socket(zmq.PUSH)
ready_sender.connect(
    f"tcp://{distributor_host}:9922"
)

print(f"[{worker_id}] Ready to receive tasks.")
print(f"[{worker_id}] Result endpoint uses port {result_port}.")

try:
    # 7. Wait until the task connection handshake succeeds.
    while True:
        event = recv_monitor_message(task_monitor)

        if event["event"] == zmq.EVENT_HANDSHAKE_SUCCEEDED:
            break

    print(f"[{worker_id}] Task connection established.")

    # 8. Tell the distributor that this worker is ready.
    ready_sender.send_string(worker_id)

    print(
        f"[{worker_id}] Sent readiness signal to distributor."
    )

    # 9. Receive one task.
    serialized_task = task_receiver.recv()

    # 10. Deserialize and validate the task.
    task = pickle.loads(serialized_task)

    if not isinstance(task, TaskMessage):
        raise TypeError("Received an invalid task message.")

    if task.operation != "sum":
        raise ValueError("Unsupported operation.")

    # 11. Calculate the sum.
    result = task.x + task.y

    print(
        f"[{worker_id}] Received task-{task.task_id}: "
        f"{task.x} + {task.y} = {result}"
    )

    # 12. Create the result message.
    result_message = ResultMessage(
        task_id=task.task_id,
        worker_id=worker_id,
        x=task.x,
        y=task.y,
        result=result,
    )

    # 13. Send the result to the collector.
    serialized_result = pickle.dumps(result_message)
    result_sender.send(serialized_result)

    print(
        f"[{worker_id}] Sent result for task-{task.task_id}."
    )

    # 14. Tell the distributor that this worker has finished.
    ready_sender.send_string(f"DONE|{worker_id}")

    print(
        f"[{worker_id}] Sent completion acknowledgment "
        f"to distributor."
    )

finally:
    # 15. Release resources.
    task_receiver.disable_monitor()
    task_monitor.close()
    task_receiver.close()
    result_sender.close()
    ready_sender.close()
    context.term()
