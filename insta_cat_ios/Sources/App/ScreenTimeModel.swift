import Foundation
import FamilyControls
import DeviceActivity
import ManagedSettings
import SwiftUI

/// 스크린 타임 권한, 감시 대상 선택, 감시 시작/중지를 담당합니다.
@MainActor
final class ScreenTimeModel: ObservableObject {

    enum AuthState {
        case unknown, denied, approved
    }

    @Published var authState: AuthState = .unknown
    @Published var selection = Settings.selection
    @Published var limitMinutes = Settings.limitMinutes
    @Published var cooldownMinutes = Settings.cooldownMinutes
    @Published var isMonitoring = false
    @Published var isShielded = Settings.isShielded
    @Published var blockedToday = Settings.blockedToday
    @Published var message: String?

    private let center = DeviceActivityCenter()
    private let store = ManagedSettingsStore()

    init() {
        refresh()
    }

    var hasTarget: Bool { !ActivitySchedule.isEmpty(selection) }

    /// 앱이 포그라운드로 돌아올 때마다 확장이 바꿔놓은 상태를 다시 읽어옵니다.
    func refresh() {
        switch AuthorizationCenter.shared.authorizationStatus {
        case .approved: authState = .approved
        case .denied: authState = .denied
        default: authState = .unknown
        }
        isMonitoring = center.activities.contains(.daily)
        isShielded = Settings.isShielded
        blockedToday = Settings.blockedToday
    }

    func requestAuthorization() async {
        do {
            try await AuthorizationCenter.shared.requestAuthorization(for: .individual)
            refresh()
        } catch {
            authState = .denied
            message = "스크린 타임 권한을 받지 못했어요: \(error.localizedDescription)"
        }
    }

    func start() {
        guard hasTarget else {
            message = "먼저 감시할 앱(인스타그램)을 골라주세요."
            return
        }

        Settings.selection = selection
        Settings.limitMinutes = limitMinutes
        Settings.cooldownMinutes = cooldownMinutes

        center.stopMonitoring([.daily, .cooldown])
        clearShield()

        do {
            try center.startMonitoring(
                .daily,
                during: ActivitySchedule.daily,
                events: [.limitReached: ActivitySchedule.limitEvent(minutes: limitMinutes,
                                                                    selection: selection)]
            )
            isMonitoring = true
            message = "고양이가 감시를 시작했어요. \(limitMinutes)분 넘기면 잡으러 옵니다."
        } catch {
            isMonitoring = false
            message = "감시를 시작하지 못했어요: \(error.localizedDescription)"
        }
    }

    func stop() {
        center.stopMonitoring([.daily, .cooldown])
        clearShield()
        isMonitoring = false
        message = "감시를 껐어요. 고양이는 자러 갑니다."
    }

    /// 차단을 지금 바로 풀어줍니다. 사용 시간 누적도 0 부터 다시 셉니다.
    func unshieldNow() {
        clearShield()
        if isMonitoring { start() }
    }

    private func clearShield() {
        store.shield.applications = nil
        store.shield.applicationCategories = nil
        store.shield.webDomains = nil
        store.shield.webDomainCategories = nil
        Settings.isShielded = false
        Settings.shieldedAt = nil
        isShielded = false
    }
}
