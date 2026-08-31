import SwiftUI
import FamilyControls

struct ContentView: View {
    @EnvironmentObject private var model: ScreenTimeModel
    @State private var showPicker = false

    private var stageMode: CatStage.Mode {
        if model.isShielded { return .angry }
        return model.isMonitoring ? .patrolling : .sleeping
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    CatStage(mode: stageMode)
                        .padding(.horizontal)

                    if model.authState != .approved {
                        authorizationCard
                    } else {
                        targetCard
                        limitCard
                        controlCard
                        statsCard
                    }

                    if let message = model.message {
                        Text(message)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }

                    limitationsNote
                }
                .padding(.vertical)
            }
            .navigationTitle("인스타 고양이")
            .familyActivityPicker(isPresented: $showPicker, selection: $model.selection)
            .onChange(of: showPicker) { isShown in
                guard !isShown else { return }
                Settings.selection = model.selection
                // 감시 중에 대상이 바뀌면 새 대상으로 다시 시작합니다.
                if model.isMonitoring { model.start() }
            }
        }
    }

    // MARK: - 카드들

    private var authorizationCard: some View {
        card {
            Text("스크린 타임 권한이 필요해요")
                .font(.headline)
            Text("iOS 는 앱이 다른 앱의 사용 시간을 알아내거나 잠그는 걸 스크린 타임(Family Controls) 을 통해서만 허용합니다. 권한을 켜야 고양이가 일을 시작할 수 있어요.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Button("권한 허용하기") {
                Task { await model.requestAuthorization() }
            }
            .buttonStyle(.borderedProminent)

            if model.authState == .denied {
                Text("거부됨 — 설정 › 스크린 타임 에서 다시 허용할 수 있어요.")
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }

    private var targetCard: some View {
        card {
            Text("감시할 앱")
                .font(.headline)
            Text(model.hasTarget
                 ? "앱 \(model.selection.applicationTokens.count)개 · 카테고리 \(model.selection.categoryTokens.count)개 선택됨"
                 : "아직 아무것도 안 골랐어요. 목록에서 인스타그램을 골라주세요.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Button(model.hasTarget ? "고르기 다시 하기" : "인스타그램 고르기") {
                showPicker = true
            }
            .buttonStyle(.bordered)
            Text("애플이 앱 목록을 가려놔서 번들 ID 로 미리 지정할 수 없고, 사용자가 직접 골라야 합니다.")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
    }

    private var limitCard: some View {
        card {
            Text("규칙")
                .font(.headline)
            Stepper("\(model.limitMinutes)분 넘게 보면 잠그기",
                    value: $model.limitMinutes, in: 1...120)
            Stepper("잠금은 \(model.cooldownMinutes)분 뒤에 풀기",
                    value: $model.cooldownMinutes, in: 15...180, step: 5)
            Text("쿨다운은 15분보다 짧게 못 잡습니다. iOS 의 DeviceActivity 스케줄 최소 길이가 15분이에요.")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .onChange(of: model.limitMinutes) { newValue in
            Settings.limitMinutes = newValue
            if model.isMonitoring { model.start() }
        }
        .onChange(of: model.cooldownMinutes) { newValue in
            Settings.cooldownMinutes = newValue
        }
    }

    private var controlCard: some View {
        card {
            if model.isMonitoring {
                Button("감시 끄기", role: .destructive) { model.stop() }
                    .buttonStyle(.bordered)
            } else {
                Button("고양이 풀어놓기") { model.start() }
                    .buttonStyle(.borderedProminent)
                    .disabled(!model.hasTarget)
            }

            if model.isShielded {
                if let remaining = Settings.minutesUntilRelease, remaining > 0 {
                    Text("지금 잠겨 있어요 — \(remaining)분 남음")
                        .font(.subheadline)
                } else {
                    Text("곧 풀립니다")
                        .font(.subheadline)
                }
                Button("지금 풀어주기 (자수)") { model.unshieldNow() }
                    .buttonStyle(.bordered)
            }
        }
    }

    private var statsCard: some View {
        card {
            HStack {
                stat(title: "오늘 걸린 횟수", value: "\(model.blockedToday)회")
                Divider()
                stat(title: "다시 터뜨린 횟수", value: "\(Settings.petCount)번")
            }
        }
    }

    private var limitationsNote: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("알아두면 좋은 것")
                .font(.caption.bold())
            Text("· 아이폰에서는 다른 앱 위에 고양이를 띄울 수 없어요. 인스타 위에 뜨는 건 잠금(Shield) 화면이고, 거기 폭발 고양이가 나옵니다.\n· 잠금 화면에는 정지 이미지만 넣을 수 있어요. 불이 움직이는 건 이 앱 안에서만 보이고, 잠금 화면은 열 때마다 폭발 장면이 한 칸씩 바뀝니다.\n· 사용 시간 집계에 1~2분 정도 오차가 생길 수 있어요. 정확한 스톱워치가 아니라 iOS 가 알려주는 시점에 반응합니다.\n· 이 앱을 지우면 잠금도 같이 풀립니다. 의지를 대신해 주지는 못해요.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal)
    }

    // MARK: - 조각

    private func stat(title: String, value: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.title3.bold())
            Text(title).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private func card<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(RoundedRectangle(cornerRadius: 18).fill(Color(.secondarySystemBackground)))
        .padding(.horizontal)
    }
}
