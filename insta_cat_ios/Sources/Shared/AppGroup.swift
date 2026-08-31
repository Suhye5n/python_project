import Foundation
import FamilyControls

/// 앱 본체와 확장(Extension)들이 같은 저장소를 보게 만드는 App Group.
/// Xcode 에서 App Group 을 새로 만들면 이 값과 project.yml 의 값을 함께 바꿔주세요.
enum AppGroup {
    static let identifier = "group.com.example.instacat"

    static var defaults: UserDefaults {
        UserDefaults(suiteName: identifier) ?? .standard
    }
}

private enum Key {
    static let selection = "selection"
    static let limitMinutes = "limitMinutes"
    static let cooldownMinutes = "cooldownMinutes"
    static let isShielded = "isShielded"
    static let shieldedAt = "shieldedAt"
    static let petCount = "petCount"
    static let blockedCount = "blockedCount"
    static let blockedCountDay = "blockedCountDay"
}

/// 앱 / 모니터 확장 / 차단 화면 확장이 공유하는 설정과 상태.
enum Settings {

    /// 감시할 앱·카테고리. 토큰은 불투명(opaque)해서 번들 ID 로는 못 고르고,
    /// 사용자가 FamilyActivityPicker 에서 직접 골라야 합니다.
    static var selection: FamilyActivitySelection {
        get {
            guard let data = AppGroup.defaults.data(forKey: Key.selection),
                  let value = try? JSONDecoder().decode(FamilyActivitySelection.self, from: data)
            else { return FamilyActivitySelection() }
            return value
        }
        set {
            let data = try? JSONEncoder().encode(newValue)
            AppGroup.defaults.set(data, forKey: Key.selection)
        }
    }

    /// 몇 분 보면 고양이가 화를 낼지. 기본 5분.
    static var limitMinutes: Int {
        get { max(1, AppGroup.defaults.object(forKey: Key.limitMinutes) as? Int ?? 5) }
        set { AppGroup.defaults.set(max(1, newValue), forKey: Key.limitMinutes) }
    }

    /// 차단이 풀릴 때까지의 대기 시간. DeviceActivity 스케줄 최소 길이가 15분이라 15분 이상만 의미가 있습니다.
    static var cooldownMinutes: Int {
        get { max(15, AppGroup.defaults.object(forKey: Key.cooldownMinutes) as? Int ?? 15) }
        set { AppGroup.defaults.set(max(15, newValue), forKey: Key.cooldownMinutes) }
    }

    static var isShielded: Bool {
        get { AppGroup.defaults.bool(forKey: Key.isShielded) }
        set { AppGroup.defaults.set(newValue, forKey: Key.isShielded) }
    }

    static var shieldedAt: Date? {
        get { AppGroup.defaults.object(forKey: Key.shieldedAt) as? Date }
        set { AppGroup.defaults.set(newValue, forKey: Key.shieldedAt) }
    }

    /// 차단 화면에서 고양이를 쓰다듬은 횟수. 순전히 재미용.
    static var petCount: Int {
        get { AppGroup.defaults.integer(forKey: Key.petCount) }
        set { AppGroup.defaults.set(newValue, forKey: Key.petCount) }
    }

    /// 오늘 몇 번이나 고양이한테 걸렸는지. 날짜가 바뀌면 0 으로 돌아갑니다.
    static var blockedToday: Int {
        get {
            guard AppGroup.defaults.string(forKey: Key.blockedCountDay) == todayKey() else { return 0 }
            return AppGroup.defaults.integer(forKey: Key.blockedCount)
        }
        set {
            AppGroup.defaults.set(todayKey(), forKey: Key.blockedCountDay)
            AppGroup.defaults.set(newValue, forKey: Key.blockedCount)
        }
    }

    /// 차단이 풀릴 때까지 남은 분. 차단 중이 아니면 nil.
    static var minutesUntilRelease: Int? {
        guard isShielded, let start = shieldedAt else { return nil }
        let remaining = TimeInterval(cooldownMinutes * 60) - Date().timeIntervalSince(start)
        return remaining > 0 ? Int(ceil(remaining / 60)) : 0
    }

    private static func todayKey() -> String {
        let c = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        return "\(c.year ?? 0)-\(c.month ?? 0)-\(c.day ?? 0)"
    }
}
