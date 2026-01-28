
# 模拟 Google Calendar API 使用文档

本文档旨在帮助开发者了解如何使用模拟的 Google Calendar API。该 API 允许你清空日历、删除事件和插入新事件。所有操作通过标准的 JSON 请求进行模拟，以便与本地系统进行交互。

---

## 1. API 概述

模拟的 API 支持以下三种操作：

- **clear**：清空指定日历的所有事件。
- **delete**：删除指定日历中的某个事件。
- **insert**：插入新的事件到指定日历中。

每个操作都需要以 JSON 格式发送请求，并会根据操作返回相应的 JSON 格式响应。

---

## 2. 请求格式

所有请求均使用标准的 JSON 格式。请求的主要字段包括：

- **action**：指定操作类型（`clear`、`delete`、`insert`）。
- **calendarID**：指定日历的 ID，所有操作都需要提供该 ID。
- **eventID**（仅在 `delete` 操作中需要）：指定要删除的事件 ID。
- **start**（仅在 `insert` 操作中需要）：事件的开始时间，格式为 `HH:MM:SS`。
- **end**（仅在 `insert` 操作中需要）：事件的结束时间，格式为 `HH:MM:SS`。
- **description**（仅在 `insert` 操作中需要）：事件的描述信息。

---

## 3. 操作说明

### 3.1 清空日历 (clear)

此操作用于清空指定日历中的所有事件。

**请求：**
```json
{
  "action": "clear",
  "calendarID": "your-calendar-id"
}
```

**响应：**
```json
{
  "status": "success",
  "message": "All events cleared from the calendar."
}
```

**说明：**
- 提供日历 ID 后，该日历中的所有事件将被清除。

---

### 3.2 删除事件 (delete)

此操作用于删除指定日历中的某个事件。

**请求：**
```json
{
  "action": "delete",
  "calendarID": "your-calendar-id",
  "eventID": "event-id-to-delete"
}
```

**响应：**
```json
{
  "status": "success",
  "message": "Event successfully deleted."
}
```

**说明：**
- 提供日历 ID 和事件 ID 后，系统将删除该事件。如果事件 ID 不存在，则返回错误信息。

---

### 3.3 插入事件 (insert)

此操作用于插入新的事件到指定日历中。

**请求：**
```json
{
  "action": "insert",
  "calendarID": "your-calendar-id",
  "start": "10:00:00",
  "end": "11:00:00",
  "description": "Meeting with Bob"
}
```

**响应：**
```json
{
  "status": "success",
  "message": "Event successfully added.",
  "eventID": "new-event-id"
}
```

**说明：**
- 提供日历 ID、开始时间、结束时间和事件描述后，系统将插入该事件。每次插入都会生成一个新的随机事件 ID。
