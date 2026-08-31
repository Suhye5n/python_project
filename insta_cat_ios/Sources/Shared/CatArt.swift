import UIKit

/// 고양이 자세. 걷기는 walkA / walkB 를 번갈아 쓰면 애니메이션이 됩니다.
enum CatPose: String, CaseIterable {
    case sit
    case walkA
    case walkB
    case sleep
    case stern
    case happy
}

/// 고양이를 코드로 직접 그립니다. 이미지 파일이 없어도 되고,
/// 앱 본체·차단 화면 확장·위젯이 전부 같은 고양이를 씁니다.
enum CatArt {

    private static let canvas: CGFloat = 100

    private static let fur     = UIColor(red: 0.96, green: 0.68, blue: 0.36, alpha: 1)
    private static let furDark = UIColor(red: 0.86, green: 0.52, blue: 0.24, alpha: 1)
    private static let belly   = UIColor(red: 1.00, green: 0.94, blue: 0.86, alpha: 1)
    private static let ink     = UIColor(red: 0.19, green: 0.13, blue: 0.10, alpha: 1)
    private static let pink    = UIColor(red: 0.97, green: 0.60, blue: 0.62, alpha: 1)
    private static let shadow  = UIColor(white: 0, alpha: 0.10)

    static func image(pose: CatPose, size: CGSize = CGSize(width: 240, height: 240)) -> UIImage {
        let format = UIGraphicsImageRendererFormat.default()
        format.opaque = false
        return UIGraphicsImageRenderer(size: size, format: format).image { context in
            let ctx = context.cgContext
            ctx.scaleBy(x: size.width / canvas, y: size.height / canvas)
            draw(pose: pose, in: ctx)
        }
    }

    static func draw(pose: CatPose, in ctx: CGContext) {
        if pose == .sleep {
            drawSleeping(in: ctx)
        } else {
            drawStanding(pose: pose, in: ctx)
        }
    }

    // MARK: - 서 있는 고양이

    private static func drawStanding(pose: CatPose, in ctx: CGContext) {
        fill(UIBezierPath(ovalIn: CGRect(x: 18, y: 84, width: 66, height: 8)), shadow, ctx)

        drawTail(pose: pose, in: ctx)

        // 다리 네 개. 걷기 자세에서는 앞/뒤가 번갈아 앞뒤로 벌어집니다.
        let swing: CGFloat = pose == .walkA ? 4 : (pose == .walkB ? -4 : 0)
        for (x, dir) in [(CGFloat(24), CGFloat(-1)), (36, 1), (55, -1), (66, 1)] {
            let offset = swing * dir
            fill(UIBezierPath(roundedRect: CGRect(x: x + offset, y: 62, width: 10, height: 26),
                              cornerRadius: 5), fur, ctx)
        }

        // 몸통과 배
        fill(UIBezierPath(roundedRect: CGRect(x: 20, y: 40, width: 58, height: 30),
                          cornerRadius: 15), fur, ctx)
        fill(UIBezierPath(ovalIn: CGRect(x: 32, y: 52, width: 38, height: 17)), belly, ctx)

        // 등 줄무늬
        for x in stride(from: CGFloat(32), through: 60, by: 11) {
            fill(UIBezierPath(roundedRect: CGRect(x: x, y: 42, width: 4, height: 11),
                              cornerRadius: 2), furDark, ctx)
        }

        drawHead(pose: pose, center: CGPoint(x: 72, y: 30), in: ctx)
    }

    private static func drawTail(pose: CatPose, in ctx: CGContext) {
        let path = UIBezierPath()
        path.move(to: CGPoint(x: 24, y: 56))
        switch pose {
        case .stern:
            // 화났을 때는 꼬리가 빳빳하게 섭니다.
            path.addCurve(to: CGPoint(x: 6, y: 16),
                          controlPoint1: CGPoint(x: 10, y: 58),
                          controlPoint2: CGPoint(x: 4, y: 38))
        case .happy:
            path.addCurve(to: CGPoint(x: 14, y: 12),
                          controlPoint1: CGPoint(x: 6, y: 52),
                          controlPoint2: CGPoint(x: 0, y: 18))
        default:
            path.addCurve(to: CGPoint(x: 10, y: 26),
                          controlPoint1: CGPoint(x: 8, y: 58),
                          controlPoint2: CGPoint(x: 2, y: 40))
        }
        stroke(path, fur, 9, ctx)
        // 꼬리 끝 하얀 털
        fill(UIBezierPath(ovalIn: CGRect(x: path.currentPoint.x - 5,
                                         y: path.currentPoint.y - 5,
                                         width: 10, height: 10)), belly, ctx)
    }

    // MARK: - 머리

    private static func drawHead(pose: CatPose, center: CGPoint, in ctx: CGContext) {
        let r: CGFloat = 17

        // 귀. 화났을 때는 뒤로 젖혀집니다.
        let earTilt: CGFloat = pose == .stern ? 5 : 0
        triangle([CGPoint(x: center.x - 14, y: center.y - 10),
                  CGPoint(x: center.x - 16 - earTilt, y: center.y - 26),
                  CGPoint(x: center.x - 2, y: center.y - 18)], fur, ctx)
        triangle([CGPoint(x: center.x + 8, y: center.y - 17),
                  CGPoint(x: center.x + 18 + earTilt, y: center.y - 27),
                  CGPoint(x: center.x + 17, y: center.y - 8)], fur, ctx)

        fill(UIBezierPath(ovalIn: CGRect(x: center.x - r, y: center.y - r,
                                         width: r * 2, height: r * 2)), fur, ctx)
        // 주둥이
        fill(UIBezierPath(ovalIn: CGRect(x: center.x - 9, y: center.y + 1,
                                         width: 18, height: 12)), belly, ctx)

        let leftEye = CGPoint(x: center.x - 7, y: center.y - 3)
        let rightEye = CGPoint(x: center.x + 7, y: center.y - 3)

        switch pose {
        case .happy:
            // ^ ^ 눈
            for eye in [leftEye, rightEye] {
                let p = UIBezierPath()
                p.move(to: CGPoint(x: eye.x - 4, y: eye.y + 2))
                p.addLine(to: CGPoint(x: eye.x, y: eye.y - 3))
                p.addLine(to: CGPoint(x: eye.x + 4, y: eye.y + 2))
                stroke(p, ink, 2, ctx)
            }
        default:
            for eye in [leftEye, rightEye] {
                fill(UIBezierPath(ovalIn: CGRect(x: eye.x - 3, y: eye.y - 4,
                                                 width: 6, height: 8)), ink, ctx)
                fill(UIBezierPath(ovalIn: CGRect(x: eye.x - 1, y: eye.y - 3,
                                                 width: 2.5, height: 2.5)), .white, ctx)
            }
        }

        if pose == .stern {
            // 찌푸린 눈썹
            for (eye, dir) in [(leftEye, CGFloat(1)), (rightEye, CGFloat(-1))] {
                let p = UIBezierPath()
                p.move(to: CGPoint(x: eye.x - 5 * dir, y: eye.y - 10))
                p.addLine(to: CGPoint(x: eye.x + 4 * dir, y: eye.y - 6))
                stroke(p, ink, 2, ctx)
            }
        }

        // 코
        triangle([CGPoint(x: center.x - 3, y: center.y + 4),
                  CGPoint(x: center.x + 3, y: center.y + 4),
                  CGPoint(x: center.x, y: center.y + 7.5)], pink, ctx)

        // 입
        let mouth = UIBezierPath()
        if pose == .stern {
            mouth.move(to: CGPoint(x: center.x - 5, y: center.y + 12))
            mouth.addQuadCurve(to: CGPoint(x: center.x + 5, y: center.y + 12),
                               controlPoint: CGPoint(x: center.x, y: center.y + 8))
        } else {
            mouth.move(to: CGPoint(x: center.x - 5, y: center.y + 8))
            mouth.addQuadCurve(to: CGPoint(x: center.x, y: center.y + 11),
                               controlPoint: CGPoint(x: center.x - 2.5, y: center.y + 11))
            mouth.addQuadCurve(to: CGPoint(x: center.x + 5, y: center.y + 8),
                               controlPoint: CGPoint(x: center.x + 2.5, y: center.y + 11))
        }
        stroke(mouth, ink, 1.6, ctx)

        drawWhiskers(center: center, in: ctx)
    }

    private static func drawWhiskers(center: CGPoint, in ctx: CGContext) {
        for dir in [CGFloat(-1), 1] {
            for dy in [CGFloat(-2), 2] {
                let p = UIBezierPath()
                p.move(to: CGPoint(x: center.x + 8 * dir, y: center.y + 5 + dy))
                p.addLine(to: CGPoint(x: center.x + 22 * dir, y: center.y + 3 + dy * 2))
                stroke(p, ink.withAlphaComponent(0.55), 1.2, ctx)
            }
        }
    }

    // MARK: - 자는 고양이

    private static func drawSleeping(in ctx: CGContext) {
        fill(UIBezierPath(ovalIn: CGRect(x: 14, y: 82, width: 74, height: 8)), shadow, ctx)

        // 몸을 동그랗게 만 자세
        fill(UIBezierPath(ovalIn: CGRect(x: 16, y: 48, width: 68, height: 38)), fur, ctx)
        fill(UIBezierPath(ovalIn: CGRect(x: 34, y: 62, width: 40, height: 22)), belly, ctx)

        // 앞으로 감아 놓은 꼬리
        let tail = UIBezierPath()
        tail.move(to: CGPoint(x: 78, y: 62))
        tail.addCurve(to: CGPoint(x: 40, y: 84),
                      controlPoint1: CGPoint(x: 92, y: 82),
                      controlPoint2: CGPoint(x: 60, y: 92))
        stroke(tail, furDark, 8, ctx)

        let center = CGPoint(x: 34, y: 52)
        triangle([CGPoint(x: center.x - 13, y: center.y - 8),
                  CGPoint(x: center.x - 16, y: center.y - 24),
                  CGPoint(x: center.x - 1, y: center.y - 16)], fur, ctx)
        triangle([CGPoint(x: center.x + 7, y: center.y - 16),
                  CGPoint(x: center.x + 18, y: center.y - 24),
                  CGPoint(x: center.x + 16, y: center.y - 7)], fur, ctx)
        fill(UIBezierPath(ovalIn: CGRect(x: center.x - 16, y: center.y - 16,
                                         width: 32, height: 32)), fur, ctx)
        fill(UIBezierPath(ovalIn: CGRect(x: center.x - 8, y: center.y + 1,
                                         width: 16, height: 11)), belly, ctx)

        // 감은 눈
        for dx in [CGFloat(-7), 7] {
            let p = UIBezierPath()
            p.move(to: CGPoint(x: center.x + dx - 4, y: center.y - 2))
            p.addQuadCurve(to: CGPoint(x: center.x + dx + 4, y: center.y - 2),
                           controlPoint: CGPoint(x: center.x + dx, y: center.y + 3))
            stroke(p, ink, 1.8, ctx)
        }
        triangle([CGPoint(x: center.x - 3, y: center.y + 4),
                  CGPoint(x: center.x + 3, y: center.y + 4),
                  CGPoint(x: center.x, y: center.y + 7.5)], pink, ctx)
        drawWhiskers(center: center, in: ctx)

        // z z z
        for (i, size) in [(0, CGFloat(9)), (1, 12), (2, 15)] {
            let text = "z" as NSString
            let attrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: size, weight: .bold),
                .foregroundColor: ink.withAlphaComponent(0.45)
            ]
            text.draw(at: CGPoint(x: 62 + CGFloat(i) * 9, y: 26 - CGFloat(i) * 11), withAttributes: attrs)
        }
    }

    // MARK: - 그리기 도우미

    private static func fill(_ path: UIBezierPath, _ color: UIColor, _ ctx: CGContext) {
        ctx.saveGState()
        color.setFill()
        path.fill()
        ctx.restoreGState()
    }

    private static func stroke(_ path: UIBezierPath, _ color: UIColor, _ width: CGFloat, _ ctx: CGContext) {
        ctx.saveGState()
        color.setStroke()
        path.lineWidth = width
        path.lineCapStyle = .round
        path.lineJoinStyle = .round
        path.stroke()
        ctx.restoreGState()
    }

    private static func triangle(_ points: [CGPoint], _ color: UIColor, _ ctx: CGContext) {
        let path = UIBezierPath()
        path.move(to: points[0])
        points.dropFirst().forEach { path.addLine(to: $0) }
        path.close()
        fill(path, color, ctx)
    }
}
