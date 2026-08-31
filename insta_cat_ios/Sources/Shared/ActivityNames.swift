import DeviceActivity
import FamilyControls

extension DeviceActivityName {
    /// 하루 동안 인스타 사용 시간을 재는 상시 감시.
    static let daily = Self("instacat.daily")
    /// 차단을 풀어줄 시각에 한 번만 깨어나는 스케줄.
    static let cooldown = Self("instacat.cooldown")
}

extension DeviceActivityEvent.Name {
    /// 사용 시간이 제한을 넘었을 때 발생하는 이벤트.
    static let limitReached = Self("instacat.limitReached")
}

enum ActivitySchedule {

    /// 하루 종일(00:00~23:59) 도는 감시 창.
    static var daily: DeviceActivitySchedule {
        DeviceActivitySchedule(
            intervalStart: DateComponents(hour: 0, minute: 0),
            intervalEnd: DateComponents(hour: 23, minute: 59),
            repeats: true
        )
    }

    /// 제한 시간 이벤트. 선택한 앱·카테고리·웹도메인 사용 시간을 모두 합산합니다.
    static func limitEvent(minutes: Int, selection: FamilyActivitySelection) -> DeviceActivityEvent {
        DeviceActivityEvent(
            applications: selection.applicationTokens,
            categories: selection.categoryTokens,
            webDomains: selection.webDomainTokens,
            threshold: DateComponents(minute: max(1, minutes))
        )
    }

    /// 선택된 게 하나라도 있는지.
    static func isEmpty(_ selection: FamilyActivitySelection) -> Bool {
        selection.applicationTokens.isEmpty
            && selection.categoryTokens.isEmpty
            && selection.webDomainTokens.isEmpty
    }
}
