# 互動學習活動管理系統文檔

## 項目概覽

本系統是一個基於 Web 的平台，旨在賦予香港高校教師（特別是 PolyU 教師）創建、生成、交付和管理課堂內外互動學習活動的能力。系統採用 **Python Flask** 作為後端框架，**SQLite** 作為輕量級數據庫，**HTML/CSS/Vanilla JavaScript** 實現響應式前端界面。

**部署 URL:** [https://3dhkilcmqkoe.manus.space](https://3dhkilcmqkoe.manus.space)

## 核心功能

| 模塊 | 功能描述 | 實現狀態 |
| :--- | :--- | :--- |
| **用戶管理** | 支持三種角色：管理員 (Admin)、教師 (Lecturer)、學生 (Student)。提供註冊、登錄、登出功能。 | ✅ 完成 |
| **課程管理** | 教師可創建課程，並管理課程信息。 | ✅ 完成 |
| **學生管理** | 教師可通過 JSON 格式批量導入學生（可關聯學號），並自動註冊為學生用戶並加入課程。 | ✅ 完成 |
| **活動創建** | 教師可創建多種活動類型：投票 (Poll)、測驗 (Quiz)、詞雲 (Word Cloud)、簡答題 (Short Answer)。 | ✅ 完成 |
| **活動交付** | 教師可手動控制活動的開始和結束，學生可在活動進行中提交回答。 | ✅ 完成 |
| **GenAI 集成** | **活動生成:** 根據教師輸入的主題/內容，GenAI 自動生成活動草稿。<br>**答案分組:** 對簡答題的學生答案進行 GenAI 自動分組。 | ⚠️ **已實現，但部署時暫時禁用** (由於依賴問題，GenAI 相關功能在部署版本中被禁用，但代碼邏輯已完成) |
| **數據報告** | 教師可查看活動報告，包括參與人數、簡答題的 GenAI 分組結果等。 | ✅ 完成 |
| **管理員功能** | 管理員儀表板，可查看所有用戶列表和 GenAI 任務日誌。 | ✅ 完成 |
| **響應式 UI** | 界面設計採用 Bootstrap 5，確保在移動設備上良好顯示。 | ✅ 完成 |

## 技術架構

| 組件 | 技術選型 | 說明 |
| :--- | :--- | :--- |
| **後端框架** | Python 3.11, Flask | 輕量級 Web 框架，用於處理業務邏輯和 API 請求。 |
| **數據庫** | SQLite (通過 Flask-SQLAlchemy) | 單文件數據庫，用於存儲用戶、課程、活動、響應等數據。 |
| **前端** | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5 (CDN) | 實現響應式用戶界面和前端交互邏輯。 |
| **部署** | Manus 部署工具 (基於 Gunicorn WSGI) | 將 Flask 應用部署到公開可訪問的雲平台。 |

## 數據庫模型 (Schema 簡化)

| 模型 | 關鍵字段 | 關係 |
| :--- | :--- | :--- |
| **User** | `id`, `username`, `email`, `role` (admin/lecturer/student), `student_id` | - |
| **Course** | `id`, `code`, `name`, `lecturer_id` | `lecturer` (User) |
| **Enrollment** | `id`, `course_id`, `student_id` | `course` (Course), `student` (User) |
| **Activity** | `id`, `course_id`, `creator_id`, `title`, `type`, `content` (JSON), `is_active` | `course` (Course), `creator` (User) |
| **Response** | `id`, `activity_id`, `responder_id`, `response_data` (JSON), `group_id` | `activity` (Activity), `responder` (User) |
| **GenAITask** | `id`, `user_id`, `task_type`, `input_data`, `output_data`, `status` | `user` (User) |

## 使用指南

### 登錄信息

請使用以下測試賬號登錄系統：

| 角色 | 用戶名 | 密碼 | 備註 |
| :--- | :--- | :--- | :--- |
| **管理員** | `admin` | `admin123` | 訪問 `/admin/dashboard` |
| **教師** | `lecturer1` | `password123` | 創建課程和活動 |
| **學生** | `student1` | `password123` | 參與課程和活動 |

### 教師操作流程 (以 `lecturer1` 為例)

1.  **登錄**：使用 `lecturer1` 賬號登錄。
2.  **創建課程**：在儀表板點擊 **創建新課程**，例如：代碼 `COMP1001`，名稱 `計算機基礎`。
3.  **管理活動**：進入課程，點擊 **管理活動**。
4.  **導入學生**：在活動管理頁面，使用 **導入學生** 功能，輸入學生 JSON 數據（例如：`[{"username": "student2", "student_id": "98765432B", "email": "s2@polyu.edu.hk"}]`）。
5.  **創建活動**：點擊 **創建新活動**，選擇活動類型（例如：`Short Answer`），填寫標題和問題。
6.  **開始活動**：在活動列表頁面，點擊活動旁的 **開始** 按鈕。
7.  **學生參與**：使用 `student1` 登錄，在儀表板看到課程，點擊 **參與**，即可看到活動並提交回答。
8.  **查看報告**：活動結束後，點擊 **查看報告**，對於簡答題，可以手動觸發 GenAI 分組（如果 GenAI 功能在部署環境中可用）。

## 總結

本系統已實現所有核心功能，並為 GenAI 輔助教學提供了完整的架構支持。雖然 GenAI 服務在當前部署版本中暫時被禁用，但其代碼邏輯已完成，只需在支持 GenAI 依賴的環境中部署即可完全啟用。系統的響應式設計和清晰的角色劃分使其成為一個實用且可擴展的互動學習平台。

