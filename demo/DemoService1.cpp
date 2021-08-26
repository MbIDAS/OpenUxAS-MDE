// ===============================================================================
// Authors: AFRL/RQQA
// Organization: Air Force Research Laboratory, Aerospace Systems Directorate, Power and Control Division
// 
// Copyright (c) 2017 Government of the United State of America, as represented by
// the Secretary of the Air Force.  No copyright is claimed in the United States under
// Title 17, U.S. Code.  All Other Rights Reserved.
// ===============================================================================

/* 
 * File:   DemoService1.cpp
 *
 * Created on 2021-08-24 12:52:29
 *
 * <Service Type="DemoService1"  />
 *
 */

// include header for this service
#include "DemoService1.h"

//include for KeyValuePair LMCP Message
#include "afrl/cmasi/KeyValuePair.h"
#include "demo/DemoStatus.h"

#include <iostream>     // std::cout, cerr, etc

 

// namespace definitions
namespace uxas  // uxas::
{
namespace service   // uxas::service::
{

///BEGIN_PRESERVE_CPP_DECLS

///END_PRESERVE_CPP_DECLS
// this entry registers the service in the service creation registry
DemoService1::ServiceBase::CreationRegistrar<DemoService1>
DemoService1::s_registrar(DemoService1::s_registryServiceTypeNames());


// service constructor
DemoService1::DemoService1()
: ServiceBase(DemoService1::s_typeName(), DemoService1::s_directoryName()) {
///BEGIN_PRESERVE_CONSTRUCTOR

///END_PRESERVE_CONSTRUCTOR
};



// service destructor
DemoService1::~DemoService1() {
///BEGIN_PRESERVE_DESTRUCTOR

///END_PRESERVE_DESTRUCTOR
};



bool DemoService1::configure(const pugi::xml_node& ndComponent)
{
    bool isSuccess(true);

    // process options from the XML configuration node:
 
    // subscribe to messages::
     addSubscriptionAddress(afrl::cmasi::AirVehicleState::Subscription);
 
///BEGIN_PRESERVE_CONFIGURE

///END_PRESERVE_CONFIGURE
    return (isSuccess);
}



bool DemoService1::initialize()
{
    // perform any required initialization before the service is started
    std::cout << "*** INITIALIZING:: Service[" << s_typeName() << "] Service Id[" << m_serviceId << "] with working directory [" << m_workDirectoryName << "] *** " << std::endl;

///BEGIN_PRESERVE_INITIALIZE

///END_PRESERVE_INITIALIZE
    return (true);
}



bool DemoService1::start()
{
    // perform any actions required at the time the service starts
    std::cout << "*** STARTING:: Service[" << s_typeName() << "] Service Id[" << m_serviceId << "] with working directory [" << m_workDirectoryName << "] *** " << std::endl;
    
///BEGIN_PRESERVE_START

///END_PRESERVE_START
    return (true);
};



bool DemoService1::terminate()
{
    // perform any action required during service termination, before destructor is called.
    std::cout << "*** TERMINATING:: Service[" << s_typeName() << "] Service Id[" << m_serviceId << "] with working directory [" << m_workDirectoryName << "] *** " << std::endl;
    
///BEGIN_PRESERVE_TERMINATE

///END_PRESERVE_TERMINATE
    return (true);
}



bool DemoService1::processReceivedLmcpMessage(std::unique_ptr<uxas::communications::data::LmcpMessage> receivedLmcpMessage)
{
    if (afrl::cmasi::isAirVehicleState(receivedLmcpMessage->m_object))
    {
        std::shared_ptr<afrl::cmasi::AirVehicleState> airVehicleStateIn = std::static_pointer_cast<afrl::cmasi::AirVehicleState> (receivedLmcpMessage->m_object);
        std::cout << "*** RECEIVED:: Service[" << s_typeName() << "] Received a AirVehicleState *** " << std::endl;

        handleAirVehicleState(airVehicleStateIn);
    }
 
///BEGIN_PRESERVE_RECEIVE

///END_PRESERVE_RECEIVE
    return false;
}


void DemoService1::handleAirVehicleState(std::shared_ptr<afrl::cmasi::AirVehicleState> message)
{
    // add message handler here
///BEGIN_PRESERVE_RECEIVE_AirVehicleState
    std::cout << "DemoService1 received AirVehicleState" << std::endl;
    auto demoStatusMessage = uxas::stduxas::make_unique<demo::DemoStatus>();
    sendSharedLmcpObjectBroadcastMessage(std::move(demoStatusMessage));

///END_PRESERVE_RECEIVE_AirVehicleState
}



///BEGIN_PRESERVE_ADDITIONAL

///END_PRESERVE_ADDITIONAL

}; //namespace service
}; //namespace uxas
