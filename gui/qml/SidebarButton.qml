import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property string iconSource: ""
    property bool isActive: false
    signal clicked()

    Layout.preferredWidth: 60
    Layout.preferredHeight: 60
    Layout.alignment: Qt.AlignHCenter

    Rectangle {
        anchors.centerIn: parent
        width: 50
        height: 50
        radius: 8
        color: root.isActive ? "#F0F0FF" : (mouseArea.containsMouse ? "#F5F5F5" : "transparent")

        Image {
            id: iconImage
            source: root.iconSource
            anchors.centerIn: parent
            width: 32
            height: 32
            fillMode: Image.PreserveAspectFit
            // Applying a color overlay effect to active icon if needed, 
            // but for now we'll just use the SVG as is.
        }
        
        // Active indicator dot/bar if desired
        Rectangle {
            visible: root.isActive
            anchors.left: parent.left
            anchors.leftMargin: -15
            anchors.verticalCenter: parent.verticalCenter
            width: 4
            height: 24
            radius: 2
            color: "#007AFF" // iOS-style blue
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
