# OpenUxAS-MDE
## A model-driven environment for OpenUxAS

## Installing OpenUxAS-MDE
To install OpenUxAS-MDE, just run the setup.py file in the root directory.
Since by default it installs to /usr/local on Linux, you'll likely need to
use sudo:
```shell
sudo python setup.py install
```
### Generating a UxAS Configuration
This project provides a domain-specific languages for defining OpenUxAS configurations, specifying messages, and defining new services.

To run the program using the existing demo configuration, do:
If you have installed OpenUxAS in its default location (~/OpenUxAS), the
generator will automatically use ~/OpenUxAS/examples as a destination directory,
and you can generate an example this way:
```shell
openuxas-mde-gen example_waterway.uxas waterway_plan.uxas
```
You can also set an environment named UXAS_EXAMPLES_DIR to point to the
OpenUxAS examples dir. Alternatively, you can specify an alternate output
directory with the `-o` option:
```shell
openuxas-mde-gen -o destdir example_waterway.uxas waterway_plan.uxas
```

If you are generating configuration both for UxAS and for AMASE, you will
always specify two files, if you are only generating UxAS configuration,
you only need the first file.

#### Destination Directory
By default, the program looks for an environment variable named UXAS_EXAMPLES_DIR
and will write the configuration files to a subdirectory in that directory
using "name:" field in the configuration file. If UXAS_EXAMPLES_DIR is not
set, but there is an OpenUxAS/examples directory under your home directory,
it will use that. If it can't find that directory,
and if no output directory is specified with the `-o` option, then
the configuration directory is created in the current directory. If you use the
`-o` option to specify an alternate directory, note that it will still
create a subdirectory there containing all the configuration files.

## Creating an OpenUxAS Configuration
OpenUxAS-MDE is designed to allow for reuse of configuration components, 
so that it should require only a small amount of configuration to create
a new project, and it should be reasonably easy to swap out pieces
of the configuration.

### The Example Waterway Configuration
To re-create the Example Waterway Search project from the OpenUxAS examples, 
you start with a configuration file like this:

```
// This is the example waterway configuration

uxas {
    Name: example_waterway
    FormatVersion: "1.0"
    EntityID: 100
    EntityType: Aircraft

    networks: [
        include "bridge_amase_standard.uxas"
    ]

    services: [
        include "standard_services.uxas"
    ]

/* Here is some stuff in a comment */

    vehicles: [
        include "waterway_vehicles.uxas"
    ]
}
```

The fields at the top: Name, FormatVersion, EntityID and EntityType are
passed directly to the cfg_example_waterway.xml file generated for
OpenUxAS. In general, you specify a field value with the format `field-name: field-value`.
The `networks` and `services` definitions show some of the reuse features
of OpenUxAS-MDE. The networks field holds the various network configurations
in a project. In this case, there is just one, and it is defined in
a file called bridge_amase_standard.uxas, which is found in the lib
directory.

The file contains this definition:
```
network LmcpObjectNetworkTcpBridge {
    TcpAddress: "tcp://127.0.0.1:5555",
    Server: false,
    Subscriptions: ["afrl.cmasi.MissionCommand",
                    "afrl.cmasi.LineSearchTask",
                    "afrl.cmasi.VehicleActionCommand"]
}
```

If you wanted to change the value of the TcpAddress, for example, you could
still include this file, and use an override directive to change
a value. For example, here is how you could change the port number
to 5678:

```
networks: [
    include "bridge_amase_standard.uxas"
    override network LmcpObjectNetworkTcpBridge {
        TcpAddress: "tcp://127.0.0.1:5678"
    }
]
```

The "network LmcpObjectNetworkBridge" indicates a type of structure (network)
and the name of this instance (LmcpObjectNetworkBridge). In an override
directive, you must provide both of these. It looks for an object
in the current sequence (in networks) with that structure type and name, and
then inserts the field values specified (e.g. replacing the TcpAddress field above).

The services part of the configuration file includes a standard set of services.
You can override settings on these services, add additional ones, either
by including them from files, or just specifying them right there in the
configuration file.

You can use the remove directive to remove a service. For example,
you could remove the RoutePlannerVisibilityService this way:

```
    services: [
        include "standard_services.uxas"
        remove service RoutePlannerVisibilityService
    ]
```

As an example of configuring a service, we can remove the
RoutePlannerVisibilityService and then include our own definition
of it:

```
services: [
    include "standard_services.uxas"
    remove service RoutePlannerVisibilityService
    service RoutePlannerVisibilityService {
        TurnRadiusOffset_m: 0.0
        MinimumWaypointSeparation_m: 52.0
    }
]
```

The vehicles part of the configuration file specifies the vehicles
that are going to be used. While you can insert the vehicles here
directly, if it is common for you to swap out sets of vehicles for
configurations, you could just have different vehicle files with
those sets, and include the one you want here.

While there is a standard_vehicles.uxas file in the lib directory,
that should just provide templates for various vehicle configurations,
and you will most likely want to customize those vehicles.
Here is the example waterway_vehicles.uxas file:

```
vehicle vehicle1 {
    ID: 400
    Label: UAV_400
    include UAV1 @ "standard_vehicles.uxas"
    state: vehicle_state {
        ID: 400
        include UAV1_state @ "standard_vehicles.uxas"
        Location: location3d {
            Series: CMASI
            Altitude: 700
            AltitudeType: MSL
            Latitude: 45.3171
            Longitude: -120.9923
        }
    }
}
vehicle vehicle2 {
    ID: 500
    Label: UAV_500
    include UAV1 @ "standard_vehicles.uxas"
    state: vehicle_state {
        ID: 500
        include UAV1_state @ "standard_vehicles.uxas"
        Location: location3d {
            Series: CMASI
            Altitude: 700
            AltitudeType: MSL
            Latitude: 45.3133
            Longitude: -120.9402
        }
    }
}
```

The `waterway_vehicles.uxas` file shows another interesting feature of
OpenUxAS-MDE: references. Notice that when it includes something from
`standard_vehicles.uxas` it has a reference "UAV1 @". That means it
will look in `standard_vehicles.uxas` for a vehicle whose name is UAV1, that is
a structure that starts with "vehicle UAV1 {". Notice also that the
ID and Label occur before the include, but these won't be overwritten by those
from the included file. The included file can only add fields that weren't
already present in the structure.

These vehicle configurations also show that you can build up a
structure by including parts from different files. In this case,
the general vehicle configuration comes from UAV1 in the
`standard_vehicles.uxas` file, while the vehicle state comes from the
UAV1_state structure in `standard_vehicles.uxas`.

When you include a single structure from a file, its fields are inserted
into the current structure (but not replacing existing fields). That is why
the Location structure just below the include of the state doesn't need
an override or remove directive. Those directives are only used when
you are including a whole file into a list of structures (i.e. if the include
is directly inside square brackets []).

### Example Waterway AMASE Configuration
While the configuration for the OpenUxAS application is reasonably
straightforward, the additional configuration for the AMASE simulator
can be a little more complicated because the configuration must create
a series of messages that will be sent by the MessageSendService. Here is
the `waterway_plan.uxas` file that generates the AMASE configuration:

```

plan {
    ScenarioData: ScenarioData {
        SimulationView: SimulationView {
            LongExtent: 0.11
            Latitude: 45.323
            Longitude: -120.9645
        }
        ScenarioName: "Waterway Search Example"
        Date: "4/15/2021:09:08:00"
        ScenarioDuration: 785
        TrackAgeOut: ""
    }
    Label: PISR_FromGoogleEarth
    Tasks: [
        task {
            include "line_search_task.uxas"
            TaskID: 1000
        }
    ]
    Entities: [ @vehicles[vehicle1].ID @vehicles[vehicle2].ID ]
    Schedule: [
        AutomationRequest {
            Series: CMASI
            ID: 1001
            Label: "PISR_FromGoogleEarth"
            TaskList: [ 1000 ]
            EntityList: [ @vehicles[vehicle1].ID, @vehicles[vehicle2].ID ]
            StartDelay: 5000
        }
    ]

    MissionCommands: [
        MissionCommand [vehicle=@vehicles] {
            Series: CMASI
            Time: 1.8
            CommandID: 100
            VehicleID: @vehicle.ID
            WaypointList: [
                Waypoint {
                    Series: CMASI
                    Number: 1
                    NextWaypoint: 1
                    Speed: @vehicle.state.Airspeed
                    SpeedType: Airspeed
                    ClimbRate: 0
                    TurnType: TurnShort
                    VehicleActionList: [
                        LoiterAction {
                            Series: CMASI
                            LoiterType: VehicleDefault
                            Radius: 100
                            Axis: 0
                            Length: 0
                            Direction: VehicleDefault
                            Duration: 0
                            Airspeed: @vehicle.state.Airspeed
                            Location: @vehicle.state.Location
                        }
                    ]
                    ContingencyWaypoint: 0
                    Altitude: @vehicle.state.Location.Altitude
                    AltitudeType: @vehicle.state.Location.AltitudeType
                    Latitude: @vehicle.state.Location.Latitude
                    Longitude: @vehicle.state.Location.Longitude
                }
            ]
            FirstWaypoint: 1
            Status: Pending
        }
    ]
}
```

The first thing to notice here is that you can make references to the
top-level networks, services, and vehicles lists in the UxAS configuration.
For example, the Entities specification looks like this:
`Entities: [ @vehicles[vehicle1].ID @vehicles[vehicle2].ID ]`

The name after the @ should be networks, services, or vehicles, although
it is almost always vehicles. A future enhancement to OpenUxAS-MDE will
allow you to define your own additional lists that can be referenced this way,
so that you might create subsets of vehicles, for example. The value in
the brackets is the name of the structure, so that `@vehicles[vehicle1.ID]`
refers to the structure in vehicles with the definition "vehicle vehicle1 {",
which you can see above in the listing for `waterway_vehicles.uxas`.

Next, the MissionCommands list lets you repeat structures for a list
of items:
```
MissionCommands: [
    MissionCommand [vehicle=@vehicles] {
```
In this case, it will iterate over all the vehicles in the vehicles list,
and each time, it will make a reference variable available named `vehicle`
(the name on the left-hand side of the = sign).

Finally, notice that the MissionCommand can reference fields in the vehicle
and traverse down several levels to do so:
```
Altitude: @vehicle.state.Location.Altitude
AltitudeType: @vehicle.state.Location.AltitudeType
Latitude: @vehicle.state.Location.Latitude
Longitude: @vehicle.state.Location.Longitude
```

## Controlling XML Generation
While openuxas-mde does have some knowledge of the structure of OpenUxAS
projects, especially with regard to what files to generate and how to structure
the resulting directories, the structure of the generated XML files is
controlled by a number of schema files in the lib directory - all with the
`.uxsch` file extension.

Here is the schema for the main uxas configuration file:
```
uxas {
    params {
        FormatVersion { type: float, required: true }
        EntityID { type: integer, required: true }
        EntityType { type: string, required: true }
        networks { type: struct network[], required: true }
        services { type: struct service[], required: true }
    }
    xml {
        tag: "UxAS"
        attr FormatVersion: FormatVersion
        attr EntityID: EntityID
        attr EntityType: EntityType

        children networks {
            render: _
        }

        children services {
            render: _
        }
    }
}
```

The `params` section gives type information about the various parameters
that should be in the uxas structure and are not actually used for XML
generation but are instead intended for type checking the OpenUxAS
configuration files.

The `xml` section specifies the XML generation. A `tag` keyword specifies
what the XML tag name is for this structure. An `attr` keyword specifies first
the name of the XML tag to generate and then the field to use for the value.
OpenUxAS-MDE generally sticks with making the field names in the structures
match the XML attribute or tag names.

The `children` keyword tells the XML generator to use the named container
(`networks` or `services` in the above example) and generate XML for
each element found in that container according to the keywords inside
the {}s. In this case the `render: _` means that it should render a
structure, which means it looks at the structure type and looks at its
various schema definitions to find the definition for that structure
type and name (name can be optional when the structures are such that
different names don't have different structures, like with vehicles). The
underscore means the current child being processed. In the declaration below,
then, the render will be repeated for every member of the `networks` container,
and each time through, the underscore will represent that member.
```
children networks {
   render: _
}
```

Here is another way the `children` keyword and the underscore can be used:
```
network LmcpObjectNetworkTcpBridge {
    xml {
        tag: "Bridge"
        attr Type: type
        attr TcpAddress: TcpAddress
        attr Server: Server
        children Subscriptions {
            tag: "SubscribeToMessage"
            attr MessageType: _
        }
    }
}
```

For this example, remember that Subscriptions in the LmcpObjectNetworkTCPBridge
were declared this way:
```
Subscriptions: ["afrl.cmasi.MissionCommand",
                "afrl.cmasi.LineSearchTask",
                "afrl.cmasi.VehicleActionCommand"]
```

Now, in the above use of the `children` keyword, it is not iterating through
a list of structures, but just a list of strings. The XML needs to have an XML
tag generated for each of these. In this case, instead of using `render`, we
use `tag` to specify the name of the XML tag that should be generated for
each member of Subscriptions, and then `attr MessageType: _` generates an attribute
named MessageType and its value each time through will be the next member of
the Subscriptions list.

This is the end result of rendering the LmcpObjectNetworkTcpBridge:
```xml
<Bridge Type="LmcpObjectNetworkTcpBridge" TcpAddress="tcp://127.0.0.1:5678" Server="false">
    <SubscribeToMessage MessageType="afrl.cmasi.MissionCommand"/>
    <SubscribeToMessage MessageType="afrl.cmasi.LineSearchTask"/>
    <SubscribeToMessage MessageType="afrl.cmasi.VehicleActionCommand"/>
</Bridge>
```

Notice that the Subscriptions were not encapsulated in any additional XML tag
but are inserted directly as children of the parent tag. Suppose, instead of the above
XML, you wanted this:
```xml
<Bridge Type="LmcpObjectNetworkTcpBridge" TcpAddress="tcp://127.0.0.1:5678" Server="false">
    <Subscriptions>
        <SubscribeToMessage MessageType="afrl.cmasi.MissionCommand"/>
        <SubscribeToMessage MessageType="afrl.cmasi.LineSearchTask"/>
        <SubscribeToMessage MessageType="afrl.cmasi.VehicleActionCommand"/>
    </Subscriptions>
</Bridge>
```

All you would have to do is add `tag "Subscriptions"` to the
children declaration, like this:
```
children Subscriptions tag "Subcriptions" {
    tag: "SubscribeToMessage"
    attr MessageType: _
}
```

Most of the OpenUxAS configuration uses XML attributes to specify data values,
but when it comes to the AMASE part of the configuration, values are often specified by
child tags. For example, here is the schema for rendering a vehicle:
```

vehicle {
    xml {
        tag: "AirVehicleConfiguration"
        attr Series: Series
        attr Time: Time
        child ID: ID
        child Label: Label
        child MinimumSpeed: MinimumSpeed
        child MaximumSpeed: MaximumSpeed
        child NominalSpeed: NominalSpeed
        child NominalAltitude: NominalAltitude
        child NominalAltitudeType: NominalAltitudeType
        render tag "NominalFlightProfile": NominalFlightProfile
        children AlternateFlightProfiles tag AlternateFlightProfiles {
            render: _
        }
        children PayloadConfigurationList tag PayloadConfigurationList {
            render: _
        }
        children AvailableLoiterTypes tag AvailableLoiterTypes {
            tag: "LoiterType"
            value: _
        }
        children AvailableTurnTypes tag AvailableTurnTypes {
            tag: "TurnType"
            value: _
        }
        child MinimumAltitude: MinimumAltitude
        child MaximumAltitude: MaximumAltitude
        child MinAltAboveGround: MinAltAboveGround
    }
}
```

Notice that it uses the `child` keyword in the same way that the `attr`
keyword works. The instruction `child MinimumSpeed: MinimumSpeed` will
create a child XML tag using the name immediately following `child` and populate
it with the field with the name following the colon. For example:
```xml
<MinimumSpeed>22.0</MinimumSpeed>
```

Notice also the `render tag "NominalFlightProfile": NominalFlightProfile`.
This is similar to `child` except that it takes the named field and renders
it using whatever schema has been defined for that structure type. In that
particular case, the NominalFlightProfile was specified with `FlightProfile {`
(in `standard_vehicles.uxas`) which creates a structure of type FlightProfile.
The XML render will then look for a renderer for type FlightProfile, which is
given in the standard_vehicles_schema.uxsch as:
```
FlightProfile {
    xml {
        tag: "FlightProfile"
        attr Series: Series
        child Name: Name
        child Airspeed: Airspeed
        child PitchAngle: PitchAngle
        child VerticalSpeed: VerticalSpeed
        child MaxBankAngle: MaxBankAngle
    }
}
```

When rendering a child tag, you may need the specify the text value of the attribute
tag, as opposed to using an attribute. For example, in the `CameraConfiguration`
structure for vehicles, there is this declaration:
```
children DiscreteHorizontalFieldOfViewList tag DiscreteHorizontalFieldOfViewList {
    tag: "real32"
    value: _
}
```
This means that for each value in the `DiscreteHorizontalFieldOfViewList`
container, it should generate a tag named `real32` and the text value
of that tag should be the next value from the `DiscreteHorizontalFieldOfViewList`
container. Here is how `DiscreteHorizontalFieldOfViewList` is defined in
the standard_vehicles.uxas file:
```
DiscreteHorizontalFieldOfViewList: [
    45.0 22.0 7.6 3.7 0.63 0.11 ]
```

The above schema declaration results in XML generation like this:
```xml
<DiscreteHorizontalFieldOfViewList>
    <real32>45.0</real32>
    <real32>22.0</real32>
    <real32>7.6</real32>
    <real32>3.7</real32>
    <real32>0.63</real32>
    <real32>0.11</real32>
</DiscreteHorizontalFieldOfViewList>
```

You have already seen in the `.uxas` file how you can make a structure repeat,
but there is also a way to do this in the XML schema. The default schema
for the `WaypointPlanManagerService` generates one such service for each vehicle, using the following
declaration:
```
xml {
    foreach vehicles {
        tag: "Service"
        attr Type: "WaypointPlanManagerService"
        attr VehicleID: vehicles.ID
        attr NumberWaypointsToServe: NumberWaypointsToServe
        attr NumberWaypointsOverlap: NumberWaypointsOverlap
        attr DefaultLoiterRadius_m: DefaultLoiterRadius_m
        attr "param.turnType": ParamTurnType
        attr AddLoiterToEndOfSegments: AddLoiterToEndOfSegments
        attr AddLoiterToEndOfMission: AddLoiterToEndOfMission
        attr LoopBackToFirstTask: LoopBackToFirstTask
        attr GimbalPayloadId: GimbalPayloadId
    }
```
In this case, it iterates through the top-level vehicles container,
and anywhere it sees `vehicles.` and a field name, it substitutes in
that field name from each successive value in vehicles. Although the
capability to do this will remain in OpenUxAS-MDE, this particular
configuration for WaypointPlanManagerService will be removed and
replaced with the mechanism for doing the repetition from the .uxas
file instead. This will give you better control in case you don't want
to generate a `WaypointPlanManagerService` for every vehicle, or if you want
to generate different configurations for different vehicles.

## Building a Setup File
To create a file that can be installed with pip, from the root directory
of the project do:
```shell
python -m build --wheel
```
The build will generate a .whl file in the `dist` directory that you can then
install with:
```shell
pip install openuxas_mde-1.0.0-py2.py3-none-any.whl
```