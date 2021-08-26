// ===============================================================================
// Authors: AFRL/RQQA
// Organization: Air Force Research Laboratory, Aerospace Systems Directorate, Power and Control Division
// 
// Copyright (c) 2017 Government of the United State of America, as represented by
// the Secretary of the Air Force.  No copyright is claimed in the United States under
// Title 17, U.S. Code.  All Other Rights Reserved.
// ===============================================================================

/* 
 * File:   DemoService2.cpp
 *
 * Created on 2021-08-24 13:02:56
 *
 * <Service Type="DemoService2"  />
 *
 */

// include header for this service
#include "DemoService2.h"

//include for KeyValuePair LMCP Message
#include "afrl/cmasi/KeyValuePair.h"

#include <iostream>     // std::cout, cerr, etc

 

// namespace definitions
namespace uxas  // uxas::
{
namespace service   // uxas::service::
{

///BEGIN_PRESERVE_CPP_DECLS

///END_PRESERVE_CPP_DECLS
// this entry registers the service in the service creation registry
DemoService2::ServiceBase::CreationRegistrar<DemoService2>
DemoService2::s_registrar(DemoService2::s_registryServiceTypeNames());


// service constructor
DemoService2::DemoService2()
: ServiceBase(DemoService2::s_typeName(), DemoService2::s_directoryName()) {
///BEGIN_PRESERVE_CONSTRUCTOR

///END_PRESERVE_CONSTRUCTOR
};



// service destructor
DemoService2::~DemoService2() {
///BEGIN_PRESERVE_DESTRUCTOR

///END_PRESERVE_DESTRUCTOR
};



bool DemoService2::configure(const pugi::xml_node& ndComponent)
{
    bool isSuccess(true);

    // process options from the XML configuration node:
 
    // subscribe to messages::
     addSubscriptionAddress(demo::DemoStatus::Subscription);
 
///BEGIN_PRESERVE_CONFIGURE

///END_PRESERVE_CONFIGURE
    return (isSuccess);
}



bool DemoService2::initialize()
{
    // perform any required initialization before the service is started
    std::cout << "*** INITIALIZING:: Service[" << s_typeName() << "] Service Id[" << m_serviceId << "] with working directory [" << m_workDirectoryName << "] *** " << std::endl;

///BEGIN_PRESERVE_INITIALIZE

///END_PRESERVE_INITIALIZE
    return (true);
}



bool DemoService2::start()
{
    // perform any actions required at the time the service starts
    std::cout << "*** STARTING:: Service[" << s_typeName() << "] Service Id[" << m_serviceId << "] with working directory [" << m_workDirectoryName << "] *** " << std::endl;
    
///BEGIN_PRESERVE_START

///END_PRESERVE_START
    return (true);
};



bool DemoService2::terminate()
{
    // perform any action required during service termination, before destructor is called.
    std::cout << "*** TERMINATING:: Service[" << s_typeName() << "] Service Id[" << m_serviceId << "] with working directory [" << m_workDirectoryName << "] *** " << std::endl;
    
///BEGIN_PRESERVE_TERMINATE

///END_PRESERVE_TERMINATE
    return (true);
}



bool DemoService2::processReceivedLmcpMessage(std::unique_ptr<uxas::communications::data::LmcpMessage> receivedLmcpMessage)
{
    if (demo::isDemoStatus(receivedLmcpMessage->m_object))
    {
        std::shared_ptr<demo::DemoStatus> demoStatusIn = std::static_pointer_cast<demo::DemoStatus> (receivedLmcpMessage->m_object);
        std::cout << "*** RECEIVED:: Service[" << s_typeName() << "] Received a DemoStatus *** " << std::endl;

        handleDemoStatus(demoStatusIn);
    }
 
///BEGIN_PRESERVE_RECEIVE

///END_PRESERVE_RECEIVE
    return false;
}


void DemoService2::handleDemoStatus(std::shared_ptr<demo::DemoStatus> message)
{
    // add message handler here
///BEGIN_PRESERVE_RECEIVE_DemoStatus
    std::cout << "DemoService2 received demo status" << std::endl;

///END_PRESERVE_RECEIVE_DemoStatus
}



///BEGIN_PRESERVE_ADDITIONAL

///END_PRESERVE_ADDITIONAL

}; //namespace service
}; //namespace uxas
