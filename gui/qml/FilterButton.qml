import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property string iconSource: ""
    property string label: ""
    property bool isActive: false
    signal clicked()

    width: 120
    height: 40

    RowLayout {
        anchors.centerIn: parent
        spacing: 8
        
        Image {
            source: root.iconSource
            width: 20
            height: 20
            fillMode: Image.PreserveAspectFit
            opacity: root.isActive ? 1.0 : 0.6
        }
        
        Text {
            text: root.label
            font.pixelSize: 14
            font.bold: root.isActive
            color: root.isActive ? "#1D1D1F" : "#86868B"
        }
    }
    
    // Bottom indicator line for active filter
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width * 0.8
        height: 2
        radius: 1
        color: "#007AFF"
        visible: root.isActive
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
        cursorShape: Qt.PointingHandCursor
    }
}
