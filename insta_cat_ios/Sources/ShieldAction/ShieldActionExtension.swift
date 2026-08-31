import ManagedSettings
import Foundation

/// 잠금 화면의 버튼을 눌렀을 때의 반응.
final class ShieldActionExtension: ShieldActionDelegate {

    override func handle(action: ShieldAction,
                         for application: ApplicationToken,
                         completionHandler: @escaping (ShieldActionResponse) -> Void) {
        completionHandler(response(for: action))
    }

    override func handle(action: ShieldAction,
                         for webDomain: WebDomainToken,
                         completionHandler: @escaping (ShieldActionResponse) -> Void) {
        completionHandler(response(for: action))
    }

    override func handle(action: ShieldAction,
                         for category: ActivityCategoryToken,
                         completionHandler: @escaping (ShieldActionResponse) -> Void) {
        completionHandler(response(for: action))
    }

    private func response(for action: ShieldAction) -> ShieldActionResponse {
        switch action {
        case .primaryButtonPressed:
            return .close
        case .secondaryButtonPressed:
            // 쓰다듬기: 잠금은 유지한 채 화면만 다시 그립니다.
            Settings.petCount += 1
            return .defer
        @unknown default:
            return .close
        }
    }
}
