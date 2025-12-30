import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Item {
    id: root
    property string iconSource: ""
    property string label: ""
    property bool isActive: false
    signal clicked()

    width: 120
    height: 40
    
    // Hover Animation
    scale: mouseArea.containsMouse ? 1.05 : 1.0
    Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

    Rectangle {
        id: bgRect
        anchors.fill: parent
        radius: height / 2
        color: root.isActive ? "#E1F0FF" : (mouseArea.containsMouse ? "#F5F5F7" : "transparent")
        border.color: root.isActive ? "#007AFF" : "transparent"
        border.width: 1
        
        Behavior on color { ColorAnimation { duration: 200 } }
        Behavior on border.color { ColorAnimation { duration: 200 } }

        RowLayout {
            anchors.centerIn: parent
            spacing: 8
            
            Image {
                id: iconImage
                source: root.iconSource
                width: 18
                height: 18
                fillMode: Image.PreserveAspectFit
                mipmap: true
                visible: false
            }
            
            ColorOverlay {
                source: iconImage
                width: 18
                height: 18
                color: root.isActive ? "#007AFF" : "#86868B"
                Behavior on color { ColorAnimation { duration: 200 } }
            }
            
            Text {
                text: root.label
                font.pixelSize: 14
                font.bold: root.isActive
                font.weight: root.isActive ? Font.DemiBold : Font.Medium
                color: root.isActive ? "#007AFF" : "#86868B"
                Behavior on color { ColorAnimation { duration: 200 } }
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
        cursorShape: Qt.PointingHandCursor
    }
}
