
import os
import pickle
import zmq

from messages import ResultMessage


# 1. Create the ZeroMQ context.
context = zmq.Context()

# 2. Create a PULL socket to receive results.
collector = context.socket(zmq.PULL)

worker1_host = os.getenv(
    "WORKER1_HOST",
    "127.0.0.1"
)
worker2_host = os.getenv(
    "WORKER2_HOST",
    "127.0.0.1"
)

collector.connect(f"tcp://{worker1_host}:9933")
collector.connect(f"tcp://{worker2_host}:9932")

# 3. Create a PUSH socket to notify the distributor.
distributor_host = os.getenv(
    "DISTRIBUTOR_HOST",
    "127.0.0.1"
)

ready_sender = context.socket(zmq.PUSH)
ready_sender.connect(
    f"tcp://{distributor_host}:9922"
)

print("[Collector] Ready to receive results from workers.")

try:
    # 4. Notify the distributor that the collector is ready.
    ready_sender.send_string("Collector")
    print("[Collector] Sent readiness signal to distributor.")

    # 5. Receive two results.
    for result_number in range(1, 3):
        serialized_result = collector.recv()

        # 6. Reconstruct and validate the result message.
        result_message = pickle.loads(serialized_result)

        if not isinstance(result_message, ResultMessage):
            raise TypeError("Received an invalid result message.")

        # 7. Display the received result.
        print(
            f"[Collector] Result {result_number}/2: "
            f"{result_message.worker_id} processed "
            f"task-{result_message.task_id}: "
            f"{result_message.x} + {result_message.y} "
            f"= {result_message.result}"
        )

    print("[Collector] All results received.")

finally:
    # 8. Release resources.
    collector.close()
    ready_sender.close()
    context.term()
