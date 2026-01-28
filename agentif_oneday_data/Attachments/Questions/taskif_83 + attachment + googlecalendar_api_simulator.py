import json
import random
import string

class CalendarSimulator:
    def __init__(self):
        self.calendar_data = {"Hk9Nw8KsRd5X": []}  # 初始化一个默认的日历

    def _generate_event_id(self):
        """生成一个随机的事件 ID"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    def _generate_calendar_id(self):
        """生成一个随机的日历 ID"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

    def clear_calendar(self, calendar_id):
        """清空指定日历的所有事件"""
        if calendar_id not in self.calendar_data:
            return {"status": "error", "message": "Calendar not found."}
        
        self.calendar_data[calendar_id] = []
        return {"status": "success", "message": "All events cleared from the calendar."}

    def delete_event(self, calendar_id, event_id):
        """删除指定日历中的某个事件"""
        if calendar_id not in self.calendar_data:
            return {"status": "error", "message": "Calendar not found."}
        
        events = self.calendar_data[calendar_id]
        for event in events:
            if event['eventID'] == event_id:
                events.remove(event)
                return {"status": "success", "message": "Event successfully deleted."}
        
        return {"status": "error", "message": "Event not found."}

    def insert_event(self, calendar_id, start, end, description):
        """插入一个新的事件到指定日历中"""
        if calendar_id is None:
            return {"status": "error", "message": "calendarID is required."}
        
        if calendar_id not in self.calendar_data:
            return {"status": "error", "message": "Calendar not found."}
        
        event_id = self._generate_event_id()
        event = {
            "eventID": event_id,
            "start": start,
            "end": end,
            "description": description
        }
        
        self.calendar_data[calendar_id].append(event)
        return {
            "status": "success",
            "message": "Event successfully added.",
            "eventID": event_id
        }


def interact_with_agent():
    simulator = CalendarSimulator()
    
    while True:
        request_str = input("请输入 JSON 请求 (或输入 'exit' 退出): ")
        
        if request_str.lower() == 'exit':
            print("退出系统。")
            break
        
        try:
            request = json.loads(request_str)
            
            action = request.get("action")
            if action == "clear":
                calendar_id = request.get("calendarID")
                response = simulator.clear_calendar(calendar_id)
            
            elif action == "delete":
                calendar_id = request.get("calendarID")
                event_id = request.get("eventID")
                response = simulator.delete_event(calendar_id, event_id)
            
            elif action == "insert":
                calendar_id = request.get("calendarID")
                start = request.get("start")
                end = request.get("end")
                description = request.get("description")
                response = simulator.insert_event(calendar_id, start, end, description)
            
            else:
                response = {"status": "error", "message": "Invalid action."}
        
        except json.JSONDecodeError:
            response = {"status": "error", "message": "Invalid JSON format."}
        
        # 输出响应结果
        print(json.dumps(response, indent=4))

if __name__ == "__main__":
    interact_with_agent()
