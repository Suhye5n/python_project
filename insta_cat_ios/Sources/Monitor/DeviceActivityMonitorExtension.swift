import DeviceActivity
import ManagedSettings
import FamilyControls
import Foundation

/// iOS 가 백그라운드에서 깨워 주는 확장. 앱이 꺼져 있어도 여기는 돌아갑니다.
final class DeviceActivityMonitorExtension: DeviceActivityMonitor {

    private let store = ManagedSettingsStore()
    private let center = DeviceActivityCenter()

    /// 제한 시간을 넘겼을 때 — 고양이가 인스타를 덮칩니다.
    override func eventDidReachThreshold(_ event: DeviceActivityEvent.Name,
                                         activity: DeviceActivityName) {
        super.eventDidReachThreshold(event, activity: activity)
        guard event == .limitReached else { return }
        applyShield()
        scheduleRelease()
    }

    /// 쿨다운 창이 시작되면 잠금을 풀고 시간 누적을 0 부터 다시 셉니다.
    override func intervalDidStart(for activity: DeviceActivityName) {
        super.intervalDidStart(for: activity)
        if activity == .cooldown { release() }
    }

    /// 하루 창이 끝날 때도 정리해 둡니다.
    override func intervalDidEnd(for activity: DeviceActivityName) {
        super.intervalDidEnd(for: activity)
        if activity == .daily { release() }
    }

    // MARK: -

    private func applyShield() {
        let selection = Settings.selection

        store.shield.applications = selection.applicationTokens.isEmpty
            ? nil : selection.applicationTokens
        store.shield.webDomains = selection.webDomainTokens.isEmpty
            ? nil : selection.webDomainTokens
        if selection.categoryTokens.isEmpty {
            store.shield.applicationCategories = nil
            store.shield.webDomainCategories = nil
        } else {
            store.shield.applicationCategories = .specific(selection.categoryTokens)
            store.shield.webDomainCategories = .specific(selection.categoryTokens)
        }

        Settings.isShielded = true
        Settings.shieldedAt = Date()
        Settings.blockedToday += 1
    }

    private func release() {
        store.shield.applications = nil
        store.shield.applicationCategories = nil
        store.shield.webDomains = nil
        store.shield.webDomainCategories = nil
        Settings.isShielded = false
        Settings.shieldedAt = nil

        center.stopMonitoring([.cooldown])
        restartDailyMonitoring()
    }

    /// 쿨다운이 끝나는 시각에 한 번 깨어나도록 별도 스케줄을 겁니다.
    /// DeviceActivitySchedule 은 창 길이가 최소 15분이어야 해서 15분짜리 창을 만들고,
    /// 창이 "시작"될 때 잠금을 풉니다.
    private func scheduleRelease() {
        let releaseAt = Date().addingTimeInterval(TimeInterval(Settings.cooldownMinutes * 60))
        let calendar = Calendar.current
        let start = calendar.dateComponents([.hour, .minute], from: releaseAt)
        let end = calendar.dateComponents([.hour, .minute],
                                          from: releaseAt.addingTimeInterval(15 * 60))

        center.stopMonitoring([.cooldown])
        try? center.startMonitoring(
            .cooldown,
            during: DeviceActivitySchedule(intervalStart: start, intervalEnd: end, repeats: false)
        )
    }

    /// 감시를 다시 걸어 누적 사용 시간을 초기화합니다.
    /// (DeviceActivity 는 창 단위로 합산하므로, 다시 시작 = 카운터 리셋입니다.)
    private func restartDailyMonitoring() {
        let selection = Settings.selection
        guard !ActivitySchedule.isEmpty(selection) else { return }

        center.stopMonitoring([.daily])
        try? center.startMonitoring(
            .daily,
            during: ActivitySchedule.daily,
            events: [.limitReached: ActivitySchedule.limitEvent(minutes: Settings.limitMinutes,
                                                                selection: selection)]
        )
    }
}
