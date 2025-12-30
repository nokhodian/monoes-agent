import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Item {
    id: root
    property string iconSource: ""
    property bool isActive: false
    signal clicked()

    Layout.preferredWidth: 60
    Layout.preferredHeight: 60
    Layout.alignment: Qt.AlignHCenter

    // Hover Animation
    scale: mouseArea.containsMouse ? 1.1 : 1.0
    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

    Rectangle {
        id: bgRect
        anchors.centerIn: parent
        width: 50
        height: 50
        radius: 16
        color: root.isActive ? "#E1F0FF" : (mouseArea.containsMouse ? "#F5F5F7" : "transparent")

        Behavior on color { ColorAnimation { duration: 200 } }

        Image {
            id: iconImage
            source: root.iconSource
            anchors.centerIn: parent
            width: 28
            height: 28
            fillMode: Image.PreserveAspectFit
            mipmap: true
            visible: false // Hidden because we use ColorOverlay
        }
        
        ColorOverlay {
            anchors.fill: iconImage
            source: iconImage
            color: root.isActive ? "#007AFF" : "#86868B"
            Behavior on color { ColorAnimation { duration: 200 } }
        }
        
        // Active indicator dot/bar - Replaced with a glow or refined indicator
        Rectangle {
            visible: root.isActive
            anchors.right: parent.right
            anchors.rightMargin: -12
            anchors.verticalCenter: parent.verticalCenter
            width: 4
            height: 20
            radius: 2
            color: "#007AFF"
        }
    }

    // Shadow for active state
    DropShadow {
        anchors.fill: bgRect
        source: bgRect
        horizontalOffset: 0
        verticalOffset: 4
        radius: 8
        samples: 17
        color: root.isActive ? "#40007AFF" : "transparent"
        visible: root.isActive
        Behavior on color { ColorAnimation { duration: 200 } }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
        cursorShape: Qt.PointingHandCursor
    }
}
