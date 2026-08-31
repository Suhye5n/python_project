import SwiftUI

@main
struct InstaCatApp: App {
    @StateObject private var model = ScreenTimeModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(model)
                .onChange(of: scenePhase) { phase in
                    // 확장(Extension)이 백그라운드에서 바꿔 놓은 차단 상태를 다시 읽어옵니다.
                    if phase == .active { model.refresh() }
                }
        }
    }
}
